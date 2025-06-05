

def concat(write_result):
    env_type = "diamond"

    head_path = f"../../envs/heads/{env_type}_head.yaml"

    args_path = f"yamls/{env_type}_env_args.yaml"

    write_path = f"../../envs/for_eva/{env_type}.yaml"

    with open(head_path, "r") as head_file:
        head = head_file.read()
        print(len(head), type(head))

    with open(args_path, "r") as args_file:
        args = args_file.read()
        print(len(args), type(args))

    concat_str = "\n".join([head, args])

    if write_result:
        with open(write_path, "w") as write_file:
            write_file.write(concat_str)
            print(f"write to {write_path}")


if __name__ == '__main__':
    concat(write_result=False)
