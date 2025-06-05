

def compute_single(predicted_step, ground_truth_step, need_compare_obj_num, print_log=False):
    # type
    if predicted_step['type'] != ground_truth_step['type']:
        return False

    # obj_name
    if "oak_" in predicted_step['obj_name'] and "oak_" not in ground_truth_step['obj_name']:
        predicted_step_obj_name = predicted_step['obj_name'].replace("oak_", "")
        if predicted_step_obj_name != ground_truth_step['obj_name']:
            return False
    else:
        if predicted_step['obj_name'] != ground_truth_step['obj_name']:
            return False

    if need_compare_obj_num:
        # obj_num
        if ground_truth_step['obj_num'] is not None:
            if 'obj_num' not in predicted_step or predicted_step['obj_num'] is None:
                if print_log:
                    print(f"{predicted_step} --- {ground_truth_step} match failed due to obj_num 1")
                return False
            else:
                if predicted_step['obj_num'] != ground_truth_step['obj_num']:
                    if print_log:
                        print(f"{predicted_step} --- {ground_truth_step} match failed due to obj_num 2")
                    return False
        else:
            # ground_truth_step没有但predicted_step有，则也说明不对
            if 'obj_num' in predicted_step and predicted_step['obj_num'] is not None:
                if print_log:
                    print(f"{predicted_step} --- {ground_truth_step} match failed due to obj_num 3")
                return False

    # tool
    if 'tool' in ground_truth_step and ground_truth_step['tool'] is not None:
        if 'tool' not in predicted_step or predicted_step['tool'] is None:
            if print_log:
                print(f"{predicted_step} --- {ground_truth_step} match failed due to tool")
            return False
        else:
            if predicted_step['tool'] != ground_truth_step['tool']:
                if print_log:
                    print(f"{predicted_step} --- {ground_truth_step} match failed due to tool")
                return False
    else:
        # ground_truth_step没有但predicted_step有，则也说明不对
        if 'tool' in predicted_step and predicted_step['tool'] is not None:
            if print_log:
                print(f"{predicted_step} --- {ground_truth_step} match failed due to tool")
            return False

    return True


def match_step(step, refer_plan, compare_with_refer=True, need_compare_obj_num=True):
    for i in range(len(refer_plan)):
        cur_refer_step = refer_plan[i]
        if compare_with_refer:
            if compute_single(step, cur_refer_step, need_compare_obj_num):
                return i
        else:
            if compute_single(cur_refer_step, step, need_compare_obj_num):
                return i
    return None


def match_step_pair(last_step, step_to_be_compare, refer_plan, compare_with_refer):
    # refer_plan是标注数据则compare_with_refer=True

    # 1. refer_plan里找能否和last_step匹配上的步骤
    match_last_step_index = match_step(last_step, refer_plan, compare_with_refer, need_compare_obj_num=False)

    # 2. refer_plan里找能否和step_to_be_compare匹配上的步骤
    match_step_to_be_compare = match_step(step_to_be_compare, refer_plan, compare_with_refer, need_compare_obj_num=True)

    # 3. 看顺序关系是否正确
    if match_last_step_index is not None and match_step_to_be_compare is not None:
        if match_last_step_index < match_step_to_be_compare:
            return True
        else:
            # stick 和 crafting_table 顺序是可以换的！
            if last_step['obj_name'] in ['stick', 'crafting_table'] and step_to_be_compare['obj_name'] in ['stick', 'crafting_table']:
                return True

    return False


def compare_two(plan_to_be_compare, refer_plan, compare_with_refer):
    # 以refer_plan为基准对比plan_to_be_compare是否正确    modified Kendall Tau

    total = 0
    correct = 0
    for index in range(len(plan_to_be_compare)):
        step_to_be_compare = plan_to_be_compare[index]
        total += 1

        if index == 0:
            # 第一个step要正确必须是refer里它也是第一个
            if index < len(refer_plan):
                refer_step = refer_plan[index]
                if compare_with_refer:
                    if compute_single(step_to_be_compare, refer_step, need_compare_obj_num=True):
                        correct += 1
                else:
                    if compute_single(refer_step, step_to_be_compare, need_compare_obj_num=True):
                        correct += 1
        else:
            # 其它的看它的相对顺序是否正确
            last_step = plan_to_be_compare[index - 1]
            if match_step_pair(last_step, step_to_be_compare, refer_plan, compare_with_refer):
                correct += 1

    return total, correct


class F1HardForPlanEva:
    def __init__(self):
        self.metric_name = "F1ScoreHard"

        self.precision_total = 0
        self.precision_correct = 0
        self.recall_total = 0
        self.recall_correct = 0

    def clear(self):
        self.precision_total = 0
        self.precision_correct = 0
        self.recall_total = 0
        self.recall_correct = 0

    def update(self, predicted_plan, ground_truth_plan):
        # precision
        precision_total, precision_correct = compare_two(predicted_plan, ground_truth_plan, compare_with_refer=True)

        # recall
        recall_total, recall_correct = compare_two(ground_truth_plan, predicted_plan, compare_with_refer=False)

        self.precision_total += precision_total
        self.precision_correct += precision_correct
        self.recall_total += recall_total
        self.recall_correct += recall_correct

        # for this plan
        precision = precision_correct / precision_total if precision_total > 0 else 0
        recall = recall_correct / recall_total if recall_total > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        precision = round(precision, 4)
        recall = round(recall, 4)
        f1 = round(f1, 4)
        return {"precision": precision, "recall": recall, "f1": f1}

    def get_result(self):
        assert self.precision_total >= self.precision_correct, "self.precision_total < self.precision_correct"
        assert self.recall_total >= self.recall_correct, "self.recall_total < self.recall_correct"

        precision = self.precision_correct / self.precision_total if self.precision_total > 0 else 0
        recall = self.recall_correct / self.recall_total if self.recall_total > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        # * 100 then round 2
        precision = round(precision * 100, 2)
        recall = round(recall * 100, 2)
        f1_score = round(f1_score * 100, 2)

        result = {
            'metric_name': self.metric_name,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
        }

        return result
