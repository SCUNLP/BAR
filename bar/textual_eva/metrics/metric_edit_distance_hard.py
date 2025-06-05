

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


def edit_distance(predicted_plan, ground_truth_plan):
    n = len(predicted_plan)
    m = len(ground_truth_plan)

    # 创建二维数组 dp，dp[i][j] 表示将 A 的前 i 个元素转换为 B 的前 j 个元素的编辑距离
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # 初始化第一行和第一列
    for i in range(n + 1):
        dp[i][0] = i  # A 的前 i 个元素转为空列表需要 i 次删除
    for j in range(m + 1):
        dp[0][j] = j  # 空列表转 B 的前 j 个元素需要 j 次插入

    # 填充 dp 数组
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if compute_single(predicted_plan[i - 1], ground_truth_plan[j - 1], need_compare_obj_num=True):
                cost = 0  # 不需要操作
            else:
                cost = 1  # 需要替换

            dp[i][j] = min(
                dp[i - 1][j] + 1,  # 删除
                dp[i][j - 1] + 1,  # 插入
                dp[i - 1][j - 1] + cost  # 替换
            )

    return dp[n][m]


class EditDistanceHardForPlanEva:
    def __init__(self):
        self.metric_name = "EditDistanceHard"

        self.task_num = 0
        self.total_len = 0
        self.edit_len = 0

    def clear(self):
        self.task_num = 0
        self.total_len = 0
        self.edit_len = 0

    def update(self, predicted_plan, ground_truth_plan):
        ed = edit_distance(predicted_plan, ground_truth_plan)

        self.task_num += 1
        self.total_len += max(len(predicted_plan), len(ground_truth_plan))
        self.edit_len += ed

        return {"edit_distance": ed}

    def get_result(self):
        avg_edit_distance = self.edit_len / self.task_num if self.task_num > 0 else 0
        edit_distance_ratio = self.edit_len / self.total_len if self.total_len > 0 else 0

        avg_edit_distance = round(avg_edit_distance, 4)
        edit_distance_ratio = round(edit_distance_ratio, 4)
        result = {
            'metric_name': self.metric_name,
            'avg_edit_distance': avg_edit_distance,
            'edit_distance_ratio': edit_distance_ratio,
        }

        return result
