import os
import re

from jarvis.assets import RECIPES_BOOKS
from jarvis.assembly.base import my_tag_items, all_tag_values

from bar.utils.rules_for_reverse_planning import fuzzy_matching_tag_items
from bar.utils.llm_tools.openai_apis.openai_api import ChatGPTTool


def prompt_decompose_pre_defined_goal(prompt: str):  # v1
    chat = [
        # system guidance
        {
            "role": "system",
            "content": "You are a helpful assistant in Minecraft. I will give you a goal to achieve in Minecraft, and you need to decompose the goal into a single step and a list of sub goals to achieve. Each step can only be in the form of ''step_type obj_num obj_name'' (e.g., craft 1 crafting_table). Output the reasoning thought and the decomposed result. You can follow the history dialogue to make the decomposition."
        },

        {
            "role": "user",
            "content": "Goal: obtain 1 wooden_pickaxe"
        },
        {
            "role": "assistant",
            "content": "Thought: Based on the given information, to obtain 1 wooden_pickaxe, the last atomic step is to craft 1 wooden_pickaxe. And we totally need to craft 1 wooden_pickaxe, so the previous sub goals are to obtain 2 stick and obtain 3 planks. Based on these analysis, the decomposed plan is as follows:\nPlan:\n1. Obtain 2 stick\n2. Obtain 3 planks\n3. Craft 1 wooden_pickaxe"
        },

        # to be decomposed
        {
            "role": "user",
            "content": prompt
        }
    ]

    return chat


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


def fix_item_name(item_name):
    if item_name == 'sticks':
        return 'stick'
    if item_name == 'iron_ores':
        return 'iron_ore'
    if item_name == 'gold_ores':
        return 'gold_ore'
    if item_name in ['log', 'Log', 'Logs']:
        return 'logs'
    if item_name in ['plank']:
        return 'planks'
    if item_name in ['coal']:
        return 'coals'
    if ' ' in item_name:
        item_name = item_name.replace(' ', '_')
    if item_name in ['wood block', 'block']:
        return "logs"

    return item_name


def parse_step_text(step_text):
    steps = []

    step_text = re.sub(r'\(.*?\)', '', step_text).strip()

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


def decompose_predefined_goal_by_model(goal: dict, llm_tool, llm_tool_name, infos):
    """
    decompose goal {'type': 'obtain', 'obj_name': 'wooden_pickaxe', 'obj_num': 1}
    """
    cur_type = goal['type']
    cur_obj_name = goal['obj_name']
    cur_obj_num = goal['obj_num']

    assert cur_type in ['obtain'], f"cur_type {goal['type']} is not supported"
    assert cur_obj_num > 0, f"cur_obj_num of {cur_obj_name} should be greater than 0"

    goal_prompt = f"Goal: obtain {cur_obj_num} {cur_obj_name}"

    # decompose by model
    input_prompt = prompt_decompose_pre_defined_goal(goal_prompt)
    output_decompose = llm_tool.chat_with_context(input_prompt)
    step, sub_goals = parse_output_decompose(output_decompose)

    print('----------------------')
    print('goal_prompt:', goal_prompt)
    print("output_decompose:", output_decompose)
    print('----------------------')

    father_decompose_ids = goal['decompose_ids']
    assert father_decompose_ids is not None and len(
        father_decompose_ids) > 0, f"father_decompose_ids is None or empty: {father_decompose_ids}"

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


if __name__ == '__main__':
    test_goal = {'type': 'obtain', 'obj_name': 'wooden_pickaxe', 'obj_num': 1, 'decompose_ids': [0]}

    test_llm_tool = ChatGPTTool("gpt-4")

    test_result = decompose_predefined_goal_by_model(test_goal, test_llm_tool, "GPT3.5", None)
    print('step:\n', test_result['step'])
    print('sub_goals:')
    for test_sub_goal in test_result['sub_goals']:
        print(test_sub_goal)
