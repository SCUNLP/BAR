import os
import argparse

from bar.utils.reverse_planning import reverse_plan
from bar.utils.llm_tools.llama3.llama3_instruct import Llama3Instruct8B
from bar.utils.llm_tools.openai_apis.openai_api import ChatGPTTool
from bar.utils import util_box


def get_plan(llm_tool, llm_tool_name, task_value):
    goal = {'type': task_value['type'], 'obj_name': task_value['obj_name'], 'obj_num': task_value['obj_num']}
    plan, other_info = reverse_plan(goal, {}, llm_tool, llm_tool_name)

    result = {'plan': plan, 'plan_tree': other_info['plan_tree']}

    return result


def run(tasks_file, llm_tool, llm_tool_name, groups_to_eva, save_path, save_results=False, overwrite_results=False):
    if os.path.exists(save_path):
        all_results = util_box.read_json(save_path)
        print('\n\n-------------------\nread results from file\n-------------------\n\n')
    else:
        all_results = {}
        print('\n\n-------------------\nno results file\n-------------------\n\n')

    for group_name in groups_to_eva:
        assert group_name in tasks_file, f"group_name {group_name} not in tasks_file"
        if group_name not in all_results:
            all_results[group_name] = {}
        # eva all items
        for task_name, task_value in tasks_file[group_name].items():
            if task_name not in all_results[group_name] or overwrite_results:
                print('\n\nStart task:', group_name, task_name)
                plan_result = get_plan(llm_tool, llm_tool_name, task_value)
                print(f"task {group_name}-{task_name} done")
                if save_results:
                    save_dict = {
                        'type': task_value['type'],
                        'obj_name': task_value['obj_name'],
                        'obj_num': task_value['obj_num'],
                        'plan': plan_result['plan'],
                        'plan_tree': plan_result['plan_tree'],
                    }
                    all_results[group_name][task_name] = save_dict
                    util_box.write_json(save_path, all_results)
                    print(f"task {group_name}-{task_name} saved")
            else:
                print(f"skip task {group_name}-{task_name}")


def load_llm(name, cuda_ip):
    if name == 'GPT3.5':
        return ChatGPTTool("gpt-3.5-turbo")
    elif name == 'GPT4':
        return ChatGPTTool("gpt-4")
    elif name == 'Llama3instruct8B':
        return Llama3Instruct8B(cuda_ip=cuda_ip)
    else:
        raise NotImplementedError(f"llm name {name} not implemented")


def run_planner():
    parser = argparse.ArgumentParser(description='Run BAR Planner')

    parser.add_argument('--tasks_file_path', type=str, default="./bar/tasks/tech_tree_tasks.json",
                        help='file of tasks to be evaluated')
    parser.add_argument('--llm_name', type=str, default='GPT4',
                        help='name of the model to be used')
    parser.add_argument('--cuda_ip', type=str, default="0",
                        help='the GPUs to be used, e.g. "0,1" for multi-GPU')
    parser.add_argument('--save_path', type=str,
                        default="textual_eva/plan_results/",
                        help='path to save the planning results')
    parser.add_argument('--groups', nargs='+',
                        default=['stone', 'iron', 'diamond', 'redstone', 'gold'],
                        help='groups to be evaluated')
    parser.add_argument('--overwrite', action='store_true',
                        help='if set, overwrite the existing results')

    args = parser.parse_args()

    # read tasks file
    tasks_file = util_box.read_json(args.tasks_file_path)

    # load model
    llm_tool = load_llm(args.llm_name, cuda_ip=args.cuda_ip)

    # path to save the results
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    save_dir = args.save_path
    save_path = os.path.join(current_dir, save_dir, f"planning_results_{args.llm_name}.json")

    # run static planning
    run(tasks_file, llm_tool, args.llm_name, args.groups, save_path, save_results=True, overwrite_results=args.overwrite)


if __name__ == '__main__':
    run_planner()
