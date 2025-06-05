

def generate_circle_env_args_sparse(circle_num, circle_thickness, gap_between_circle, gap_between_origin_point, fill_upper_height, fill_lower_height, fill_name, ratio, minimal_fill_length):
    # 在agent出生点四周生成圆圈状矿石分布

    # circle_num = 8  # 多少个圈一共
    # circle_thickness = 4  # 圈的厚度
    # gap_between_circle = 4  # 圈与圈之间的间隔
    # gap_between_origin_point = 6  # 圈与出生点之间的间隔
    #
    # fill_upper_height = -23  # 圈的上界高度
    # fill_lower_height = -40  # 圈的下界高度

    # 环境规则限制，一条fill指令最大的填充数量为32768
    max_fill_num = 32000

    # 开始按需生成yaml
    lines = []

    for fill_height in range(fill_upper_height, fill_lower_height-1, -1):
        for circle_index in range(circle_num):
            cur_circle_num = circle_index + 1
            # 生成这一层圆环的fill指令，按4条边依次生成
            # 例如，第一层第一个圈的上边的fill指令为：- /fill ~-10 ~10 ~-23 ~10 ~10 ~-23 minecraft:iron_ore

            # 上边 ----------------------------------------------------------------
            upper_edge_x1 = - (gap_between_origin_point + circle_thickness * cur_circle_num + gap_between_circle * circle_index)
            upper_edge_z1 = - upper_edge_x1
            upper_edge_y1 = fill_height

            upper_edge_x2 = - upper_edge_x1
            upper_edge_z2 = upper_edge_z1 - circle_thickness + 1  # 为正数
            upper_edge_y2 = fill_height

            # 下边 ----------------------------------------------------------------
            lower_edge_x1 = upper_edge_x1
            lower_edge_z1 = - upper_edge_z1  # 为负数
            lower_edge_y1 = fill_height

            lower_edge_x2 = upper_edge_x2
            lower_edge_z2 = - upper_edge_z2
            lower_edge_y2 = fill_height

            # 左边 ----------------------------------------------------------------
            left_edge_x1 = upper_edge_x1
            left_edge_z1 = upper_edge_z2 - 1  # 为正数
            left_edge_y1 = fill_height

            left_edge_x2 = left_edge_x1 + circle_thickness - 1
            left_edge_z2 = - left_edge_z1  # 为负数
            left_edge_y2 = fill_height

            # 右边 ----------------------------------------------------------------
            right_edge_x1 = - left_edge_x1
            right_edge_z1 = left_edge_z1
            right_edge_y1 = fill_height

            right_edge_x2 = - left_edge_x2
            right_edge_z2 = left_edge_z2
            right_edge_y2 = fill_height

            # print(f"\nfrom {upper_edge_x1} {upper_edge_y1} {upper_edge_z1} to {upper_edge_x2} {upper_edge_y2} {upper_edge_z2}")
            # print(f"from {lower_edge_x1} {lower_edge_y1} {lower_edge_z1} to {lower_edge_x2} {lower_edge_y2} {lower_edge_z2}")
            # print(f"from {left_edge_x1} {left_edge_y1} {left_edge_z1} to {left_edge_x2} {left_edge_y2} {left_edge_z2}")
            # print(f"from {right_edge_x1} {right_edge_y1} {right_edge_z1} to {right_edge_x2} {right_edge_y2} {right_edge_z2}")
            # print('---')

            lines.extend(generate_one_edge_fill_command_sparse(upper_edge_x1, upper_edge_y1, upper_edge_z1, upper_edge_x2, upper_edge_y2, upper_edge_z2, fill_name, max_fill_num, "upper", ratio, minimal_fill_length))
            lines.extend(generate_one_edge_fill_command_sparse(lower_edge_x1, lower_edge_y1, lower_edge_z1, lower_edge_x2, lower_edge_y2, lower_edge_z2, fill_name, max_fill_num, "lower", ratio, minimal_fill_length))
            lines.extend(generate_one_edge_fill_command_sparse(left_edge_x1, left_edge_y1, left_edge_z1, left_edge_x2, left_edge_y2, left_edge_z2, fill_name, max_fill_num, "left", ratio, minimal_fill_length))
            lines.extend(generate_one_edge_fill_command_sparse(right_edge_x1, right_edge_y1, right_edge_z1, right_edge_x2, right_edge_y2, right_edge_z2, fill_name, max_fill_num, "right", ratio, minimal_fill_length))

    return lines


def generate_one_edge_fill_command_sparse(x1, y1, z1, x2, y2, z2, block_type, max_fill_num, edge_type, ratio, minimal_fill_length=2):
    assert minimal_fill_length >= 2, f"minimal_fill_length {minimal_fill_length} < 2"

    # 计算总的填充数量
    total_fill_num = (abs(x1 - x2) + 1) * (abs(y1 - y2) + 1) * (abs(z1 - z2) + 1)

    assert total_fill_num <= max_fill_num, f"total_fill_num {total_fill_num} > max_fill_num {max_fill_num}"

    fill_commands = []

    # 稀疏填充，按ratio比例填充

    # 计算每隔几个点填充一次，例如，ratio=0.1，那么每隔10个点填充一次
    fill_interval = int(1 / ratio)

    if edge_type in ["upper", "lower"]:
        # 也就是把原来的x1 z1 ---> x2 z2的区域，按照ratio的比例，分成多个小区域，每个小区域按概率填充或者不填充或者均匀分布
        # 先把x1 z1 ---> x2 z2的区域，按照minimal_fill_length，分成多个小区域
        assert x1 < x2, f"x1 {x1} >= x2 {x2}"

        pass_num = 0
        cur_x1 = x1
        while cur_x1 < x2:
            pass_num += 1

            cur_x2 = cur_x1 + minimal_fill_length - 1
            cur_x2 = min(cur_x2, x2)
            if pass_num % fill_interval == 0:
                fill_commands.append(f"  - /fill ~{cur_x1} ~{y1} ~{z1} ~{cur_x2} ~{y2} ~{z2} {block_type}")
            cur_x1 = cur_x2 + 1

    elif edge_type in ["left", "right"]:
        # 也就是把原来的x1 z1 ---> x2 z2的区域，按照ratio的比例，分成多个小区域，每个小区域按概率填充或者不填充或者均匀分布
        # 先把x1 z1 ---> x2 z2的区域，按照minimal_fill_length，分成多个小区域
        assert z1 > z2, f"z1 {z1} >= z2 {z2}"  # z2负 z1正

        pass_num = 0
        cur_z1 = z1
        while cur_z1 > z2:
            pass_num += 1

            cur_z2 = cur_z1 - minimal_fill_length + 1
            cur_z2 = max(cur_z2, z2)
            if pass_num % fill_interval == 0:
                fill_commands.append(f"  - /fill ~{x1} ~{y1} ~{cur_z1} ~{x2} ~{y2} ~{cur_z2} {block_type}")
            cur_z1 = cur_z2 - 1
    else:
        raise ValueError(f"edge_type {edge_type} not in ['upper', 'lower', 'left', 'right']")

    return fill_commands


def generate_one_edge_fill_command(x1, y1, z1, x2, y2, z2, block_type, max_fill_num):
    # 是有可能一次无法填充完的，所以需要多次填充

    # 计算总的填充数量
    total_fill_num = (abs(x1 - x2) + 1) * (abs(y1 - y2) + 1) * (abs(z1 - z2) + 1)

    assert total_fill_num <= max_fill_num, f"total_fill_num {total_fill_num} > max_fill_num {max_fill_num}"

    fill_commands = []

    #  - /fill ~-35 ~-30 ~-35 ~-34 ~-29 ~-34 minecraft:iron_ore
    fill_commands.append(f"  - /fill ~{x1} ~{y1} ~{z1} ~{x2} ~{y2} ~{z2} {block_type}")

    return fill_commands


def generate_circle_env_args(circle_num, circle_thickness, gap_between_circle, gap_between_origin_point, fill_upper_height, fill_lower_height, fill_name):
    # 在agent出生点四周生成圆圈状矿石分布

    # circle_num = 8  # 多少个圈一共
    # circle_thickness = 4  # 圈的厚度
    # gap_between_circle = 4  # 圈与圈之间的间隔
    # gap_between_origin_point = 6  # 圈与出生点之间的间隔
    #
    # fill_upper_height = -23  # 圈的上界高度
    # fill_lower_height = -40  # 圈的下界高度

    # 环境规则限制，一条fill指令最大的填充数量为32768
    max_fill_num = 32000

    # 开始按需生成yaml
    lines = []

    for fill_height in range(fill_upper_height, fill_lower_height-1, -1):
        for circle_index in range(circle_num):
            cur_circle_num = circle_index + 1
            # 生成这一层圆环的fill指令，按4条边依次生成
            # 例如，第一层第一个圈的上边的fill指令为：- /fill ~-10 ~10 ~-23 ~10 ~10 ~-23 minecraft:iron_ore

            # 上边 ----------------------------------------------------------------
            upper_edge_x1 = - (gap_between_origin_point + circle_thickness * cur_circle_num + gap_between_circle * circle_index)
            upper_edge_z1 = - upper_edge_x1
            upper_edge_y1 = fill_height

            upper_edge_x2 = - upper_edge_x1
            upper_edge_z2 = upper_edge_z1 - circle_thickness + 1
            upper_edge_y2 = fill_height

            # 下边 ----------------------------------------------------------------
            lower_edge_x1 = upper_edge_x1
            lower_edge_z1 = - upper_edge_z1
            lower_edge_y1 = fill_height

            lower_edge_x2 = upper_edge_x2
            lower_edge_z2 = - upper_edge_z2
            lower_edge_y2 = fill_height

            # 左边 ----------------------------------------------------------------
            left_edge_x1 = upper_edge_x1
            left_edge_z1 = upper_edge_z2 - 1
            left_edge_y1 = fill_height

            left_edge_x2 = left_edge_x1 + circle_thickness - 1
            left_edge_z2 = - left_edge_z1
            left_edge_y2 = fill_height

            # 右边 ----------------------------------------------------------------
            right_edge_x1 = - left_edge_x1
            right_edge_z1 = left_edge_z1
            right_edge_y1 = fill_height

            right_edge_x2 = - left_edge_x2
            right_edge_z2 = left_edge_z2
            right_edge_y2 = fill_height

            # print(f"\nfrom {upper_edge_x1} {upper_edge_y1} {upper_edge_z1} to {upper_edge_x2} {upper_edge_y2} {upper_edge_z2}")
            # print(f"from {lower_edge_x1} {lower_edge_y1} {lower_edge_z1} to {lower_edge_x2} {lower_edge_y2} {lower_edge_z2}")
            # print(f"from {left_edge_x1} {left_edge_y1} {left_edge_z1} to {left_edge_x2} {left_edge_y2} {left_edge_z2}")
            # print(f"from {right_edge_x1} {right_edge_y1} {right_edge_z1} to {right_edge_x2} {right_edge_y2} {right_edge_z2}")
            # print('---')

            lines.extend(generate_one_edge_fill_command(upper_edge_x1, upper_edge_y1, upper_edge_z1, upper_edge_x2, upper_edge_y2, upper_edge_z2, fill_name, max_fill_num))
            lines.extend(generate_one_edge_fill_command(lower_edge_x1, lower_edge_y1, lower_edge_z1, lower_edge_x2, lower_edge_y2, lower_edge_z2, fill_name, max_fill_num))
            lines.extend(generate_one_edge_fill_command(left_edge_x1, left_edge_y1, left_edge_z1, left_edge_x2, left_edge_y2, left_edge_z2, fill_name, max_fill_num))
            lines.extend(generate_one_edge_fill_command(right_edge_x1, right_edge_y1, right_edge_z1, right_edge_x2, right_edge_y2, right_edge_z2, fill_name, max_fill_num))

    return lines


def generate_gold_env_args(write_result):
    result_file_path = "yamls/gold_env_args.yaml"

    all_lines = []

    # -23 -> -27 minecraft:iron_ore
    iron_ore_lines = generate_circle_env_args(
        circle_num=8,
        circle_thickness=4,
        gap_between_circle=4,
        gap_between_origin_point=6,
        fill_upper_height=-23,
        fill_lower_height=-27,
        fill_name="minecraft:iron_ore",
    )
    all_lines.extend(iron_ore_lines)

    # -33 -> -37 minecraft:gold_ore 稀疏放置
    gold_ore_lines = generate_circle_env_args_sparse(
        circle_num=4,
        circle_thickness=3,
        gap_between_circle=6,
        gap_between_origin_point=10,
        fill_upper_height=-33,
        fill_lower_height=-37,
        fill_name="minecraft:gold_ore",
        ratio=0.2,  # 0.5 0.33 0.25 0.2 1/6 1/7 1/8
        minimal_fill_length=2
    )
    all_lines.extend(gold_ore_lines)

    # write
    if write_result:
        with open(result_file_path, 'w') as f:
            write_str = "\n".join(all_lines)
            f.write(write_str)
        print(f"write to {result_file_path} done")


def generate_redstone_env_args(write_result):
    result_file_path = "yamls/redstone_env_args.yaml"

    all_lines = []

    # -23 -> -27 minecraft:iron_ore
    iron_ore_lines = generate_circle_env_args(
        circle_num=8,
        circle_thickness=4,
        gap_between_circle=4,
        gap_between_origin_point=6,
        fill_upper_height=-23,
        fill_lower_height=-27,
        fill_name="minecraft:iron_ore",
    )
    all_lines.extend(iron_ore_lines)

    # -33 -> -37 minecraft:redstone_ore 稀疏放置
    gold_ore_lines = generate_circle_env_args_sparse(
        circle_num=4,
        circle_thickness=3,
        gap_between_circle=6,
        gap_between_origin_point=10,
        fill_upper_height=-33,
        fill_lower_height=-37,
        fill_name="minecraft:redstone_ore",
        ratio=0.2,  # 0.5 0.33 0.25 0.2 1/6 1/7 1/8
        minimal_fill_length=2
    )
    all_lines.extend(gold_ore_lines)

    # write
    if write_result:
        with open(result_file_path, 'w') as f:
            write_str = "\n".join(all_lines)
            f.write(write_str)
        print(f"write to {result_file_path} done")


def generate_diamond_env_args(write_result):
    result_file_path = "yamls/diamond_env_args.yaml"

    all_lines = []

    # -23 -> -27 minecraft:iron_ore
    iron_ore_lines = generate_circle_env_args(
        circle_num=8,
        circle_thickness=4,
        gap_between_circle=4,
        gap_between_origin_point=6,
        fill_upper_height=-23,
        fill_lower_height=-27,
        fill_name="minecraft:iron_ore",
    )
    all_lines.extend(iron_ore_lines)

    # -43 -> -47 minecraft:diamond_ore 稀疏放置  /give @p minecraft:diamond_ore 64
    gold_ore_lines = generate_circle_env_args_sparse(
        circle_num=4,
        circle_thickness=3,
        gap_between_circle=6,
        gap_between_origin_point=10,
        fill_upper_height=-43,
        fill_lower_height=-47,
        fill_name="minecraft:diamond_ore",
        ratio=1/8,  # 0.5 0.33 0.25 0.2 1/6 1/7 1/8
        minimal_fill_length=2
    )
    all_lines.extend(gold_ore_lines)

    # write
    if write_result:
        with open(result_file_path, 'w') as f:
            write_str = "\n".join(all_lines)
            f.write(write_str)
        print(f"write to {result_file_path} done")


def generate(write_result):
    # generate_iron_env_args(write_result)

    # generate_gold_env_args(write_result)

    # generate_redstone_env_args(write_result)

    generate_diamond_env_args(write_result)


if __name__ == '__main__':
    generate(write_result=True)
