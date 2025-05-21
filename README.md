# BAR
Code for our ACL 2025 Paper ["BAR: A Backward Reasoning based Agent for Complex Minecraft Tasks"](https://arxiv.org/abs/2505.14079)

![BAR](/imgs/method.png "BAR")

<p align="center">Our proposed backward reasoning based agent</p>

### About BAR
Large language model (LLM) based agents have shown great potential in following human instructions and automatically completing various tasks. To complete a task, the agent needs to decompose it into easily executed steps by planning.
Existing studies mainly conduct the planning by inferring what steps should be executed next starting from the agent's initial state. However, this forward reasoning paradigm doesn't work well for complex tasks.
We propose to study this issue in Minecraft, a virtual environment that simulates complex tasks based on real-world scenarios. We believe that the failure of forward reasoning is caused by the big perception gap between the agent's initial state and task goal. 
To this end, we leverage backward reasoning and make the planning starting from the terminal state, which can directly achieve the task goal in one step. Specifically, we design a BAckward Reasoning based agent (BAR). It is equipped with a recursive goal decomposition module, a state consistency maintaining module and a stage memory module to make robust, consistent, and efficient planning starting from the terminal state. Experimental results demonstrate the superiority of BAR over existing methods and the effectiveness of proposed modules.

### Code
coming soon
