

def compute_single(predicted_step, ground_truth_step):
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

    # obj_num
    if ground_truth_step['obj_num'] is not None:
        if 'obj_num' not in predicted_step or predicted_step['obj_num'] is None:
            return False
        else:
            if predicted_step['obj_num'] != ground_truth_step['obj_num']:
                return False
    else:
        # ground_truth_step没有但predicted_step有，则也说明不对
        if 'obj_num' in predicted_step and predicted_step['obj_num'] is not None:
            return False

    # tool
    if 'tool' in ground_truth_step and ground_truth_step['tool'] is not None:
        if 'tool' not in predicted_step or predicted_step['tool'] is None:
            return False
        else:
            if predicted_step['tool'] != ground_truth_step['tool']:
                return False
    else:
        # ground_truth_step没有但predicted_step有，则也说明不对
        if 'tool' in predicted_step and predicted_step['tool'] is not None:
            return False

    return True


class AccHardForPlanEva:
    def __init__(self):
        self.metric_name = "AccuracyHard"

        self.total_step = 0
        self.correct_step = 0

    def clear(self):
        self.total_step = 0
        self.correct_step = 0

    def update(self, predicted_plan, ground_truth_plan):
        total_this = 0
        correct_this = 0
        for index, step in enumerate(ground_truth_plan):
            self.total_step += 1
            total_this += 1

            if index >= len(predicted_plan):
                break

            if compute_single(predicted_plan[index], step):
                self.correct_step += 1
                correct_this += 1

        acc = correct_this / total_this if total_this > 0 else 0
        acc = round(acc, 4)

        return {"acc": acc}

    def get_result(self):
        acc = self.correct_step / self.total_step if self.total_step > 0 else 0
        # * 100 then round 2
        acc = acc * 100
        acc = round(acc, 2)

        result = {
            'metric_name': self.metric_name,
            'acc': acc,
            'total_step': self.total_step,
            'correct_step': self.correct_step,
        }

        return result

