# BAR: A Backward Reasoning based Agent for Complex Minecraft Tasks

![BAR](/imgs/bar.png "BAR")

<p align="center">Our proposed backward reasoning based agent</p>

### About BAR
Large language model (LLM) based agents have shown great potential in following human instructions and automatically completing various tasks. To complete a task, the agent needs to decompose it into easily executed steps by planning.
Existing studies mainly conduct the planning by inferring what steps should be executed next starting from the agent's initial state. However, this forward reasoning paradigm doesn't work well for complex tasks.
We propose to study this issue in Minecraft, a virtual environment that simulates complex tasks based on real-world scenarios. We believe that the failure of forward reasoning is caused by the big perception gap between the agent's initial state and task goal. 
To this end, we leverage backward reasoning and make the planning starting from the terminal state, which can directly achieve the task goal in one step. Specifically, we design a BAckward Reasoning based agent (BAR). It is equipped with a recursive goal decomposition module, a state consistency maintaining module and a stage memory module to make robust, consistent, and efficient planning starting from the terminal state.

## Install Dependencies

### Prepare the Environment

We recommend using Anaconda to manage the environment. If you don't have Anaconda installed, you can download it from [here](https://www.anaconda.com/products/distribution).

```bash
conda create -n bar python=3.10
conda activate bar
```

Make sure you have JDK 8 installed. If you don't have it installed, you can install it using the following command:

```bash
conda install openjdk=8
```

To check your JDK version, run the command `java -version`:

```bash
openjdk version "1.8.0_392"
OpenJDK Runtime Environment (build 1.8.0_392-8u392-ga-1~20.04-b08)
OpenJDK 64-Bit Server VM (build 25.392-b08, mixed mode)
```

### Install BAR

Clone the repository:
```bash
git clone https://github.com/WitcherLeo/BAR.git
```


As we use the same environment as [JARVIS-1](https://github.com/CraftJarvis/JARVIS-1), you need to download the MCP environment from [this link](https://drive.google.com/file/d/1NLcEFNJXipQpop2JsmcSxfbFHWKJWv6c/view?usp=sharing)  
Then unzip the file `stark_tech.zip` to the path `jarvis/stark_tech`


Then you can install BAR as a Python package.
```bash
pip install -e .
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

## Usage

You need to set the environment variable `OPENAI_API_KEY` and `OPENAI_API_BASE` first.
```bash
export OPENAI_API_KEY="sk-******"
export OPENAI_API_BASE="your openai base url"
```

Then you can run the following command to start the static planning for the BAR agent.
```bash
python -m bar.run_planner --llm_name GPT4 --cuda_ip 0 --groups stone iron diamond --overwrite
```


## To-Do
- [ ] Release `dynamic planning` environment and code.
- [ ] Release `customization BAR` to enable users to customize their own BAR agents.


## Check out our paper!
Our paper is available on [Arxiv](https://arxiv.org/pdf/2505.14079). Please cite our paper if you find **BAR** useful for your research:
```
@article{du2025bar,
  title={BAR: A Backward Reasoning based Agent for Complex Minecraft Tasks},
  author={Du, Weihong and Liao, Wenrui and Yan, Binyu and Liang, Hongru and Cohn, Anthony G and Lei, Wenqiang},
  journal={arXiv preprint arXiv:2505.14079},
  year={2025}
}
```
