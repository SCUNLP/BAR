import os
import jsonlines

from bar.textual_eva.metrics.metric_acc_hard import AccHardForPlanEva
from bar.textual_eva.metrics.metric_edit_distance_hard import EditDistanceHardForPlanEva
from bar.textual_eva.metrics.metric_f1_hard import F1HardForPlanEva
from bar.utils import util_box


def read_ground_truth():
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    ground_truth_base_dir = os.path.join(current_dir, "ground_truth")

    groups_to_read = [
        'stone',
        'iron',
        'gold',
        'redstone',
        'diamond',
    ]

    ground_truth = {}

    for group_name in groups_to_read:
        group_path = os.path.join(ground_truth_base_dir, group_name)
        assert os.path.exists(group_path), f"group_path {group_path} not exists"

        ground_truth_this_group = {}
        for task_name in os.listdir(group_path):
            task_path = os.path.join(group_path, task_name)
            with jsonlines.open(task_path) as f:
                plan = []
                for line in f:
                    plan.append(line)
            task_name_no_suffix = task_name.split('.')[0]
            ground_truth_this_group[task_name_no_suffix] = plan

        ground_truth[group_name] = ground_truth_this_group

    return ground_truth


def load_metric(metric_name):
    if metric_name == "AccuracyHard":
        return AccHardForPlanEva()
    elif metric_name == "F1ScoreHard":
        return F1HardForPlanEva()
    elif metric_name == "EditDistanceHard":
        return EditDistanceHardForPlanEva()

    else:
        raise Exception(f"metric_name {metric_name} not supported")


def eva(read_plan_path, groups_to_eva, llm_name, metric_names, eva_results_save_path, save_results, overwrite_results):
    read_plan = util_box.read_json(read_plan_path)

    print('read_plan.keys():', read_plan.keys())

    ground_truth = read_ground_truth()

    metrics = [load_metric(metric_name) for metric_name in metric_names]

    if os.path.exists(eva_results_save_path):
        eva_results = util_box.read_json(eva_results_save_path)
        print(f'\n\n-------------------\nread eva_results from file: {eva_results_save_path}\n-------------------\n\n')
    else:
        eva_results = {}
        print('\n\n-------------------\nno eva_results file\n-------------------\n\n')

    if llm_name not in eva_results:
        eva_results[llm_name] = {}

    tmp_results = {}
    # eva each group
    for group_name in groups_to_eva:
        assert group_name in read_plan, f"group_name {group_name} not in read_plan"
        assert group_name in ground_truth, f"group_name {group_name} not in ground_truth"

        for metric_index in range(len(metrics)):
            metrics[metric_index].clear()

        # eva this group
        for task_name, task_value in read_plan[group_name].items():
            assert task_name in ground_truth[group_name], f"task_name {task_name} not in ground_truth"

            predicted_plan = task_value['plan']
            ground_truth_plan = ground_truth[group_name][task_name]

            res_this_plan = {}
            for metric_index in range(len(metrics)):
                res_this_plan[metrics[metric_index].metric_name] = metrics[metric_index].update(predicted_plan, ground_truth_plan)

        result_this_group = {}
        for metric_index in range(len(metrics)):
            result_this_group[metrics[metric_index].metric_name] = metrics[metric_index].get_result()

        tmp_results[group_name] = result_this_group

        if group_name not in eva_results[llm_name] or overwrite_results:
            eva_results[llm_name][group_name] = result_this_group

            res_texts = []
            for key, value in result_this_group[metrics[0].metric_name].items():
                if key in ['metric_name']:
                    continue
                res_texts.append(f"{key}: {value}")
            res_text = "\n".join(res_texts)
            res_text = f"------\n{llm_name} - {group_name} result:\n{res_text}\n------\n"
            print(res_text)

        if save_results:
            util_box.write_json(eva_results_save_path, eva_results)
            print(f"eva_results saved to {eva_results_save_path}")

    # end of group evaluation -----------------------------------------------

    metric_key_map = {
        "AccuracyHard": "acc",
        "F1ScoreHard": "f1_score",
        "EditDistanceHard": "avg_edit_distance",
    }

    # results for all metrics
    print_results = []
    for group_name in groups_to_eva:
        group_result = tmp_results[group_name]
        for metric_index in range(len(metrics)):
            metric_result = group_result[metrics[metric_index].metric_name]
            target_result = metric_result[metric_key_map[metrics[metric_index].metric_name]]
            print_results.append(target_result)

    # print results
    print("\t".join([str(result) for i, result in enumerate(print_results)]))

    print("   ".join([str(result) + " |" if (i != 0 and (i + 1) % len(metrics) == 0) else str(result) for i, result in enumerate(print_results)]))


def eva_main(save_results, overwrite_results):
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)

    llm_name = 'GPT4_ours'

    read_plan_path = os.path.join(current_dir, f"plan_results/planning_results_GPT4.json")  # 要评估的plan来源

    metric_names = ["AccuracyHard", "F1ScoreHard", "EditDistanceHard"]

    eva_results_save_path = os.path.join(current_dir, f"eva_results/textual_eva_results.json")

    groups_to_eva = [
        'stone',
        'iron',
        'diamond',
        'redstone',
        'gold',
     ]

    eva(read_plan_path, groups_to_eva, llm_name, metric_names, eva_results_save_path, save_results, overwrite_results)


if __name__ == '__main__':
    eva_main(save_results=False, overwrite_results=False)
