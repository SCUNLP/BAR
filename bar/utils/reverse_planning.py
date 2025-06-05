import os
import re
from queue import Queue

from jarvis.assets import RECIPES_BOOKS
from jarvis.assembly.base import my_tag_items, all_tag_values

from bar.utils.decompose_predefined import decompose_predefined_goal_by_model
from bar.utils.rules_for_reverse_planning import fuzzy_matching_tag_items, \
    optimize_placement, post_process_plan, fuse_repeated_step_loose
from bar.utils.llm_tools.openai_apis.openai_api import ChatGPTTool
from bar.utils.llm_tools.llama3.llama3_instruct import Llama3Instruct8B


def prompt_decompose_goal(goal: str):  # v3.2
    chat = [
        # system guidance
        {
            "role": "system",
            "content": "You are a helpful assistant in Minecraft. I will give you a goal to achieve in Minecraft, and you need to decompose the goal into a single step and a list of sub goals to achieve. Each step can only be in the form of ''step_type obj_num obj_name'' (e.g., craft 1 crafting_table). Output the reasoning thought and the decomposed result. You can follow the history dialogue to make the decomposition."
        },

        {
            "role": "user",
            "content": "Goal: collect 3 cobblestone."
        },
        {
            "role": "assistant",
            "content": "Thought: to collect 3 cobblestone, the last step is to mine 3 cobblestone with wooden_pickaxe, as mining the cobblestone requires at least wooden_pickaxe. And the previous sub goals are to obtain 1 wooden_pickaxe and dig down with wooden_pickaxe, because cobblestone only appears at the below ground level. Based on these analysis, the decomposed result is as follows:\nPlan:\n1. Obtain 1 wooden_pickaxe\n2. Dig down with wooden_pickaxe\n3. Mine 3 cobblestone with wooden_pickaxe"
        },

        {
            "role": "user",
            "content": f"Goal: {goal}."
        }
    ]

    return chat


def fix_item_name(item_name):
    if item_name == 'sticks':
        return 'stick'
    if item_name == 'iron_ores':
        return 'iron_ore'
    if item_name == 'gold_ores':
        return 'gold_ore'
    if item_name in ['log', 'Log', 'Logs']:
        return 'logs'
    if item_name in ['plank', 'wooden_plank', 'wooden_planks', 'oak_wooden_plank', 'oak_wooden_planks', 'oak_plank']:
        return 'planks'
    if item_name in ['coal']:
        return 'coals'
    if item_name in ['slab']:
        return 'oak_slab'
    if item_name in ['gold_nuggets']:
        return 'gold_nugget'
    if item_name in ['torches']:
        return 'torch'
    if item_name in ['wooden_slabs', 'wooden_slab']:
        return 'oak_slab'
    if ' ' in item_name:
        item_name = item_name.replace(' ', '_')
    if item_name in ['wood block']:
        return "logs"

    return item_name


def parse_step_text(step_text):
    steps = []

    if step_text[-1] == '.':
        step_text = step_text[:-1]

    assert len(step_text) > 0, f"step_text is empty: {step_text}"

    # tool: do something with tool_name ----------------------------------------------------------------------------------------------------
    parsed_tool = None
    if 'with' in step_text:
        step_text_mine_split = step_text.split('with')
        assert len(step_text_mine_split) == 2, f"先解析tool --- step_text split failed: {step_text}"
        tool = step_text_mine_split[1].strip().lower()
        assert len(tool) > 0, f"先解析tool --- tool is empty: {step_text}"
        if tool != "barehand" and ('minecraft:' + tool not in all_tag_values) and ('minecraft:' + tool not in my_tag_items.keys()):
            fuzzy_tool = fuzzy_matching_tag_items(tool)
            if fuzzy_tool:
                tool = fuzzy_tool
            else:
                raise Exception("tool not in my_tag_items:", step_text, tool)
        if "hand" not in tool:
            parsed_tool = tool
        step_text = step_text_mine_split[0].strip()

    # special ----------------------------------------------------------------------------------------------------
    # 1. dig down
    if step_text.lower() == 'dig down':
        steps.append({
            'type': 'special',
            'obj_name': 'dig down',
            'obj_num': None,
            'tool': parsed_tool
        })
        return steps
    # 2. look straight ahead
    if step_text.lower() == 'look straight ahead':
        steps.append({
            'type': 'special',
            'obj_name': 'look straight ahead',
            'obj_num': None,
            'tool': parsed_tool
        })
        return steps
    # 3. explore the surroundings
    if step_text.lower().startswith('explore'):
        steps.append({
            'type': 'special',
            'obj_name': 'explore the surroundings',
            'obj_num': None,
            'tool': parsed_tool
        })
        return steps

    if re.match(r'^[a-zA-Z]+[0-9]+', step_text):  # 如果有字母和数字连在一起
        step_text = re.sub(r'([a-zA-Z]+)([0-9]+)', r'\1 \2', step_text)  # 则在字母和数字之间加空格

    # 1. parse type
    step_type_split = step_text.split(' ')
    if len(step_type_split) < 2:
        raise Exception("Step type parsing failed in step_type_re:", step_text)

    step_type_text = step_type_split[0].lower()

    STEP_TYPE = ['mine', 'craft', 'smelt', 'obtain', 'collect']  # 解析出来即包含原子动作，也包含目标的类型
    if step_type_text not in STEP_TYPE:
        # text goal
        return [{
            'type': 'text',
            'obj_name': step_text,
            'obj_num': None,
            'tool': parsed_tool
        }]

    step_type = step_type_text

    # 2. parse obj
    obj_re = re.search(r'\d+', step_text).group()
    if not obj_re:
        raise Exception("obj_num parsing failed in step_text:", step_text)
    obj_num = int(obj_re)
    assert obj_num > 0, f"obj_num is not positive in step_text: {step_text}"

    obj_name_split = step_text.split(' ')
    if len(obj_name_split) < 2:
        raise Exception("obj_name parsing failed in step_text:", step_text)
    obj_name = obj_name_split[-1].strip().lower()
    if obj_name[-1] == '.':
        obj_name = obj_name[:-1]
    assert len(obj_name) > 0, f"obj_name is empty in step_text: {step_text}"

    obj_name = fix_item_name(obj_name)
    if step_type not in ['mine', 'collect']:
        if ('minecraft:' + obj_name not in my_tag_items.keys()) and ('minecraft:' + obj_name not in all_tag_values):
            raise Exception("obj_name not in my_tag_items:", step_text, obj_name)

    step_dict = {
        'type': step_type,
        'obj_name': obj_name,
        'obj_num': obj_num,
        'tool': parsed_tool
    }
    steps.append(step_dict)

    assert len(steps) > 0, f"No steps parsed from the step text: {step_text}"

    return steps


def parse_output_decompose(output_text: str):
    output_text = output_text.strip()
    lines = output_text.split('\n')

    step_texts = []
    for line in lines:
        line = line.strip()
        # 只取以数字开头的行，用re判断
        if re.match(r'^\d+\.', line):
            # 去掉数字和点后加入列表
            pure_text = re.sub(r'^\d+\.', '', line).strip()
            step_texts.append(pure_text)

    if len(step_texts) == 0:
        raise Exception("parse_output_decompose --- No steps found in the output text: " + output_text)

    # parse each step
    sub_goals = []
    for step_text in step_texts:
        sub_goals.extend(parse_step_text(step_text))
    assert len(sub_goals) > 0, "parse_output_decompose --- No steps parsed from the output text: " + output_text

    # 由于返回的sub_goals会进入队列导致最终给出的plan里的step的顺序和现在给的是反的，所以这里要reverse
    sub_goals.reverse()

    step = sub_goals[0]
    sub_goals = sub_goals[1:]

    return step, sub_goals


def decompose_goal(goal: dict, llm_tool, llm_tool_name, infos):
    """
    decompose the goal into a single step and a list of sub goals to achieve.
    """
    goal_type = goal['type']
    assert goal_type in ['text', 'collect'], f"goal['type'] {goal_type} is not supported"

    if goal_type == 'collect':
        goal_text = f"collect {goal['obj_num']} {goal['obj_name']}"
    elif goal_type == 'text':
        goal_text = goal['obj_name']
    else:
        raise Exception("goal_type is not supported:", goal_type)

    chat_decompose = prompt_decompose_goal(goal_text)
    output_decompose = llm_tool.chat_with_context(chat_decompose)
    step, sub_goals = parse_output_decompose(output_decompose)

    print('----------------------')
    print('goal_text:', goal_text)
    print("output_decompose:", output_decompose)
    print('----------------------')

    father_decompose_ids = goal['decompose_ids']
    assert father_decompose_ids is not None and len(father_decompose_ids) > 0, f"father_decompose_ids is None or empty: {father_decompose_ids}"

    for i in range(len(sub_goals)):
        give_index = len(sub_goals) - 1 - i
        assert give_index >= 0
        new_decompose_ids = father_decompose_ids + [give_index]
        sub_goals[i]['decompose_ids'] = new_decompose_ids
    step['decompose_ids'] = father_decompose_ids + [len(sub_goals)]

    for sub_goal in sub_goals:
        if sub_goal['type'] == 'obtain':
            if sub_goal['obj_name'] not in ["logs", "coals", "wooden_slabs", "planks", "oak_planks", "spruce_planks", "birch_planks", "jungle_planks", "acacia_planks", "dark_oak_planks", "crimson_planks", "warped_planks"]:
                assert sub_goal['obj_name'] in RECIPES_BOOKS, f"obj_name {sub_goal['obj_name']} is not in RECIPES_BOOKS"

    return {'step': step, 'sub_goals': sub_goals}


def reverse_plan(goal: dict, inventory: dict, llm_tool, llm_tool_name=None):
    plan_queue = Queue()  # The queue for storing the goals to be processed

    plan_stack = []  # The stack for storing the processed steps

    plan_tree = {  # record the plan tree
        'goal': goal,  # overall goal
        'units': []  # each unit is a dict with 'goal' and 'decompose_result'
    }

    # decompose_ids used to track the decomposition process
    init_decompose_ids = [0,]
    goal['decompose_ids'] = init_decompose_ids

    # init
    plan_queue.put(goal)

    # flag
    craft_crafting_table = False
    craft_furnace = False
    # supporting infos for the LLM tool
    infos = {
    }

    while not plan_queue.empty():
        # 1. get the top goal
        top_goal = plan_queue.get()

        if top_goal['type'] == 'placement':
            assert 'decompose_ids' in top_goal and top_goal['decompose_ids'] is not None, f"top_goal['decompose_ids'] is None: {top_goal}"
            plan_stack.append(top_goal)
            continue

        # 2. check if the top goal need to be decomposed
        top_goal_type = top_goal['type']
        top_goal_obj_name = top_goal['obj_name']
        top_goal_obj_num = top_goal['obj_num']

        if top_goal_type in ['mine', 'craft', 'equip', 'smelt', 'special']:
            need_decompose = False
        elif top_goal_type in ['collect']:
            if top_goal_obj_name in ['logs', 'dark_oak_log', 'oak_log', 'acacia_log', 'birch_log', 'jungle_log', 'spruce_log',
                                     'dark_oak_logs', 'oak_logs', 'acacia_logs', 'birch_logs', 'jungle_logs', 'spruce_logs',
                                     'logs_that_burn']:
                need_decompose = False
                top_goal['type'] = 'mine'
                top_goal['obj_name'] = 'logs'
            elif top_goal_obj_name in ['string']:
                need_decompose = False
                top_goal['type'] = 'mine'
                top_goal['obj_name'] = 'string'
            else:
                need_decompose = True
        else:
            need_decompose = True

        if not need_decompose:
            assert 'decompose_ids' in top_goal and top_goal[
                'decompose_ids'] is not None, f"top_goal['decompose_ids'] is None: {top_goal}"
            plan_stack.append(top_goal)
            continue

        # 3. decompose the top goal based on its type

        # try-except to avoid the LLM API error
        max_attempts = 50
        attempts = 0

        while attempts < max_attempts:
            try:
                if top_goal_type in ['obtain']:
                    decompose_result = decompose_predefined_goal_by_model(top_goal, llm_tool, llm_tool_name, infos)
                elif top_goal_type in ['text', 'collect']:
                    decompose_result = decompose_goal(top_goal, llm_tool, llm_tool_name, infos)
                else:
                    raise Exception(f"top_goal_type {top_goal_type} is not supported")
                break
            except Exception as e:
                print(f"Attempt {attempts} failed with error: {str(e)}")
                attempts += 1

        if attempts >= max_attempts:
            raise Exception(f"Failed to run the code after {max_attempts} attempts")

        # store the decompose result as a unit in the plan tree
        cur_unit = {
            'goal': top_goal,
            'decompose_result': decompose_result
        }
        plan_tree['units'].append(cur_unit)

        assert type(decompose_result['step']) is dict, f"decompose_result['step'] is not dict: {decompose_result['step']}"
        assert type(decompose_result['sub_goals']) is list, f"decompose_result['sub_goals'] is not list: {decompose_result['sub_goals']}"

        assert 'decompose_ids' in decompose_result['step'] and decompose_result['step']['decompose_ids'] is not None, f"decompose_result['step']['decompose_ids'] is None: {decompose_result['step']}"
        plan_stack.append(decompose_result['step'])

        if decompose_result['step']['type'] == 'craft' and decompose_result['step']['obj_name'] not in ['planks', 'crafting_table', 'stick',
     "oak_planks",
     "spruce_planks",
     "birch_planks",
     "jungle_planks",
     "acacia_planks",
     "dark_oak_planks",
     "crimson_planks",
     "warped_planks"]:
            cur_decompose_result_step_decompose_ids = decompose_result['step']['decompose_ids'].copy()  # copy以确保不影响原来的decompose_ids
            cur_decompose_result_step_decompose_ids[-1] += 1
            if not craft_crafting_table:
                # add craft crafting_table to queue
                plan_queue.put({'type': 'obtain', 'obj_name': 'crafting_table', 'obj_num': 1, 'decompose_ids': cur_decompose_result_step_decompose_ids})
                craft_crafting_table = True
            else:
                # add craft crafting_table placement for further optimization
                plan_queue.put({'type': 'placement', 'obj_name': 'craft 1 crafting_table', 'obj_num': 0, 'decompose_ids': cur_decompose_result_step_decompose_ids})

        if decompose_result['step']['type'] == 'smelt':
            cur_decompose_result_step_decompose_ids = decompose_result['step']['decompose_ids'].copy()  # copy以确保不影响原来的decompose_ids
            cur_decompose_result_step_decompose_ids[-1] += 1
            if not craft_furnace:
                # add craft furnace to queue
                plan_queue.put({'type': 'obtain', 'obj_name': 'furnace', 'obj_num': 1, 'decompose_ids': cur_decompose_result_step_decompose_ids})
                craft_furnace = True
            else:
                # add craft furnace placement for further optimization
                plan_queue.put({'type': 'placement', 'obj_name': 'craft 1 furnace', 'obj_num': 0, 'decompose_ids': cur_decompose_result_step_decompose_ids})

        sub_goals = decompose_result['sub_goals']
        for sub_goal in sub_goals:
            plan_queue.put(sub_goal)

    plan = []
    while len(plan_stack) > 0:
        plan.append(plan_stack.pop())

    plan = fuse_repeated_step_loose(plan)

    plan = optimize_placement(plan)

    plan = post_process_plan(plan)

    print('\n\n-------------\nfinal plan:')
    for step in plan:
        print(step)
    print('\n\n')

    return plan, {'plan_tree': plan_tree}


if __name__ == '__main__':
    test_goal = {'type': 'obtain', 'obj_name': 'crafting_table', 'obj_num': 1}

    test_llm_tool = ChatGPTTool("gpt-4")

    test_plan = reverse_plan(test_goal, {}, test_llm_tool, llm_tool_name='GPT4')

    print('goal:', test_goal)
    print("plan:")
    for test_step in test_plan:
        print(test_step)
