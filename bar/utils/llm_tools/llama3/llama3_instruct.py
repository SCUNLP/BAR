import torch
from transformers import AutoTokenizer, LlamaForCausalLM
import re


class Llama3Instruct8B(object):
    def __init__(self, cuda_ip=None):
        self.model_path = "/path/to/Meta-Llama-3-8B-Instruct"

        if cuda_ip:
            self.cuda_list = str(cuda_ip).split(',')
        else:
            self.cuda_list = '0'.split(',')

        # load the model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

        # Setting `pad_token_id` to `eos_token_id`:128001 for open-end generation.
        self.tokenizer.pad_token = self.tokenizer.eos_token

        self.memory = '47GiB'
        self.max_memory = {int(cuda): self.memory for cuda in self.cuda_list}

        # load base model
        self.model = LlamaForCausalLM.from_pretrained(
            self.model_path,
            device_map="auto",
            max_memory=self.max_memory)

        print('model loaded')

    def generate(self, input_text, max_length=2048):
        input_ids = self.tokenizer.encode(input_text, return_tensors='pt').to(self.model.device)
        output_ids = self.model.generate(input_ids, max_length=max_length, do_sample=False)  # Content Length: 4k
        output = self.tokenizer.decode(output_ids[:, input_ids.shape[1]:][0], skip_special_tokens=True)
        return output

    def batch_generate(self, input_texts, max_length=2048):
        input_ids = self.tokenizer.batch_encode_plus(input_texts, return_tensors='pt', padding="longest", truncation=True).to(self.model.device)
        output_ids = self.model.generate(input_ids['input_ids'], attention_mask=input_ids['attention_mask'],
                                         max_length=max_length, do_sample=False)
        output = self.tokenizer.batch_decode(output_ids[:, input_ids['input_ids'].shape[1]:], skip_special_tokens=True)
        return output

    def chat_with_context(self, chat, max_length=2048):
        input_ids = self.tokenizer.apply_chat_template(chat, return_tensors='pt').to(self.model.device)
        attention_mask = torch.ones(input_ids.shape, dtype=torch.long, device=self.model.device)

        output_ids = self.model.generate(input_ids, attention_mask=attention_mask, max_length=max_length, pad_token_id=self.tokenizer.eos_token_id,
                                         do_sample=True, top_k=50, top_p=0.95, temperature=0.7)

        output = self.tokenizer.decode(output_ids[:, input_ids.shape[1]:][0], skip_special_tokens=True)

        # use re to remove the assistant prefix
        output = output.strip()
        output = re.sub(r'^assistant', '', output)
        output = output.strip()

        return output
