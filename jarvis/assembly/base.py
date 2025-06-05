import time

from jarvis.utils import write_video

# from openai import OpenAI
# client = OpenAI()

import json
from jarvis.assets import TASKS_FILE, TAG_ITEMS_FILE, SPAWN_FILE, SKILL_FILE, MY_SKILL_FILE, MINE_TAG_ITEMS_FILE, SMELT_TAG_ITEMS_FILE, MY_TAG_ITEMS_FILE

with open(TASKS_FILE, 'r') as f:
    jarvis_tasks = json.load(f)

def get_task_config(task_name):
    task_dict = {}
    for task in jarvis_tasks:
        if task['task'] == task_name:
            task_dict = task
            return task_dict
    return {}

with open(TAG_ITEMS_FILE, 'r') as f:
    tag_items = json.load(f)

with open(MY_TAG_ITEMS_FILE, 'r') as f:
    my_tag_items = json.load(f)
    all_tag_values = []
    for key, value in my_tag_items.items():
        all_tag_values += value

# mine_tag_items
with open(MINE_TAG_ITEMS_FILE, 'r') as f:
    mine_tag_items = json.load(f)
    all_mine_items = []
    for key, value in mine_tag_items.items():
            all_mine_items += value

# smelt_tag_items
with open(SMELT_TAG_ITEMS_FILE, 'r') as f:
    smelt_tag_items = json.load(f)
    all_smelt_items = []
    for key, value in smelt_tag_items.items():
            all_smelt_items += value

with open(SKILL_FILE, 'r') as f:
    skills = json.load(f)

# MODIFIED
with open(MY_SKILL_FILE, 'r') as f:
    my_skills = json.load(f)

from jarvis.assets import MEMORY_FILE
with open(MEMORY_FILE, 'r') as f:
    memory = json.load(f)

class MarkBase:
    
    def __init__(self, **kwargs):
        pass
        
    def reset(self):
        self.record_frames = []
        self.record_infos = []
    
    def do(self):
        raise NotImplementedError

    def record_step(self):
        record_frames = getattr(self, 'record_frames', [])
        record_infos = getattr(self, 'record_infos', [])
        self.record_frames = record_frames + [self.info['pov']]
        self.record_infos = record_infos + [self.info]

    def make_traj_video(self, output_path: str):
        if getattr(self, 'record_frames', None) is None:
            return
        write_video(self.record_frames, output_path)



