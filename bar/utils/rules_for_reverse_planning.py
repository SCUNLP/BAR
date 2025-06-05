

def fuzzy_matching_tag_items(text):
    # wooden --------------------------------------------------------------------------
    if "wooden" in text:
        if "pickaxe" in text:
            return "wooden_pickaxe"
        elif "axe" in text:
            return "wooden_axe"
        elif "shovel" in text:
            return "wooden_shovel"
        elif "hoe" in text:
            return "wooden_hoe"
        elif "sword" in text:
            return "wooden_sword"
        else:
            return None
    return None

    # stone ---------------------------------------------------------------------------


def fuse_repeated_step_loose(plan):
    """
    宽松一点进行合并，不严格要求
    """
    assert len(plan) > 0, f"len(plan) is 0"

    # 合并连续的相同的step，例如，两个mine logs 1，合并为mine logs 2，并且合并之后被合并的step要被删除
    delete_steps = [False] * len(plan)

    # 为了确保可以正确删除多余的步骤，第一次只先合并mine，然后再合并其他的

    # Round 1 --- fuse mine step
    for i in range(len(plan)):
        if delete_steps[i]:
            continue
        cur_step = plan[i]
        # 有些类型的step不需要合并
        if cur_step['type'] not in ['mine']:
            continue

        cur_step_type = cur_step['type']
        cur_obj_name = cur_step['obj_name']
        cur_obj_num = cur_step['obj_num']
        if 'tool' in cur_step:
            cur_tool = cur_step['tool']
        else:
            cur_tool = None

        for j in range(i+1, len(plan)):
            if delete_steps[j]:
                continue
            fuse_flag = False

            next_step = plan[j]
            next_step_type = next_step['type']
            next_obj_name = next_step['obj_name']
            next_obj_num = next_step['obj_num']
            if 'tool' in next_step:
                next_tool = next_step['tool']
            else:
                next_tool = None
            next_decompose_ids = next_step['decompose_ids']
            assert len(next_decompose_ids) > 0, f"len(next_decompose_ids) is 0"

            # 带有tool的step合并和其他的有区别，分开处理
            if cur_step_type == next_step_type and cur_obj_name == next_obj_name:
                # 如果有tool则tool也要相同
                if cur_tool is not None:
                    if next_tool is not None and cur_tool == next_tool:
                        cur_obj_num += next_obj_num
                        delete_steps[j] = True
                        fuse_flag = True
                else:
                    if next_tool is None:
                        cur_obj_num += next_obj_num
                        delete_steps[j] = True
                        fuse_flag = True

            if fuse_flag:
                # 特殊情况，由于拆解时很多相邻的step实际上有绑定的关系，但其中某个step被合并后导致遗留了多余的step，这部分step应该被删除
                # 从头到尾遍历一遍所有step，当前next_step对应的同一级步骤以及子步骤都应该被删除
                if cur_obj_name in ['cobblestone', 'iron_ore', 'gold_ore', 'redstone', 'diamond']:
                    delete_decompose_ids = next_decompose_ids[:-1]
                    assert len(delete_decompose_ids) > 0, f"len(delete_decompose_ids) is 0"
                    delete_decompose_ids_len = len(delete_decompose_ids)
                    delete_decompose_ids_str = "".join([str(item) for item in delete_decompose_ids])

                    for new_index in range(len(plan)):
                        if delete_steps[new_index]:
                            continue
                        new_index_decompose_ids = plan[new_index]['decompose_ids']
                        # new_index_decompose_ids至少长度要和delete_decompose_ids一样长，不然没法比较
                        if len(new_index_decompose_ids) >= len(next_decompose_ids):
                            new_index_decompose_ids_to_compare = new_index_decompose_ids[:delete_decompose_ids_len]
                            new_index_decompose_ids_to_compare_str = "".join([str(item) for item in new_index_decompose_ids_to_compare])
                            if delete_decompose_ids_str == new_index_decompose_ids_to_compare_str:
                                delete_steps[new_index] = True
                                # print(f'\n\ndelete:\n{next_decompose_ids}\n{new_index_decompose_ids}\n\n')

        # 更新cur_step的obj_num
        plan[i]['obj_num'] = cur_obj_num

    plan_after_round1 = []
    for i in range(len(plan)):
        if not delete_steps[i]:
            plan_after_round1.append(plan[i])

    # Round 2 --- fuse other steps
    seen_steps = [False] * len(plan_after_round1)
    plan_after_round2 = []

    for i in range(len(plan_after_round1)):
        if seen_steps[i]:
            continue
        cur_step = plan_after_round1[i]
        # 有些类型的step不需要合并
        if cur_step['type'] in ['special', 'mine']:
            plan_after_round2.append(cur_step)
            seen_steps[i] = True
            continue

        cur_step_type = cur_step['type']
        cur_obj_name = cur_step['obj_name']
        cur_obj_num = cur_step['obj_num']
        if 'tool' in cur_step:
            cur_tool = cur_step['tool']
        else:
            cur_tool = None

        for j in range(i+1, len(plan_after_round1)):
            if seen_steps[j]:
                continue
            # fuse_flag = False

            next_step = plan_after_round1[j]
            next_step_type = next_step['type']
            next_obj_name = next_step['obj_name']
            next_obj_num = next_step['obj_num']
            if 'tool' in next_step:
                next_tool = next_step['tool']
            else:
                next_tool = None

            if next_step_type in ['special']:
                continue

            # 带有tool的step合并和其他的有区别，分开处理
            if cur_step_type in ['craft', 'smelt', 'placement']:
                if cur_step_type == next_step_type and cur_obj_name == next_obj_name:
                    cur_obj_num += next_obj_num
                    seen_steps[j] = True
                    fuse_flag = True
            else:
                # raise NotImplementedError(f"cur_step_type {cur_step_type} is not supported")
                pass

        plan_after_round2.append({'type': cur_step['type'], 'obj_name': cur_obj_name, 'obj_num': cur_obj_num, 'tool': cur_tool})
        seen_steps[i] = True

    return plan_after_round2


def optimize_placement(plan):
    new_plan = []

    put_crafting_table_placement = False  # 是否已经用placement放置了crafting_table
    put_furnace_placement = False  # 是否已经用placement放置了furnace

    for item in plan:
        if item['type'] in ['placement']:
            if item['obj_name'] == 'craft 1 crafting_table':
                new_plan.append({'type': 'craft', 'obj_name': 'crafting_table', 'obj_num': 1})
                put_crafting_table_placement = True
            elif item['obj_name'] == 'craft 1 furnace':
                new_plan.append({'type': 'craft', 'obj_name': 'furnace', 'obj_num': 1})
                put_furnace_placement = True
            else:
                raise NotImplementedError(f"placement item['obj_name'] {item['obj_name']} is not supported")
        else:
            if item['type'] in ['craft']:
                if item['obj_name'] in ['crafting_table']:
                    if put_crafting_table_placement:
                        continue
                    else:
                        new_plan.append(item)
                elif item['obj_name'] in ['furnace']:
                    if put_furnace_placement:
                        continue
                    else:
                        new_plan.append(item)
                else:
                    new_plan.append(item)
            else:
                new_plan.append(item)

    return new_plan


def post_process_plan(plan):
    # 删除decompose_id字段 同时处理pickaxe有多个的情况
    for i in range(len(plan)):
        if 'decompose_ids' in plan[i]:
            # 把decompose_ids字段删除
            del plan[i]['decompose_ids']

    return plan


