import os

def replace_config_path(option):
    before1, after1 = 'data/config.json', '/root/fumble_capital_tools/data/config.json'
    before2, after2 = 'data/keywords.json', '/root/fumble_capital_tools/data/keywords.json'
    if option == 2:
        after1, before1 = 'data/config.json', '/root/fumble_capital_tools/data/config.json'
        after2, before2 = 'data/keywords.json', '/root/fumble_capital_tools/data/keywords.json'
    
    file_paths = ['general_tools.py', 'pumpfun_monitor.py', 'success_tool.py']
    
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"The file {file_path} does not exist.")
            return

        with open(file_path, 'r') as file:
            content = file.read()

        new_content = content.replace(before1, after1)
        new_content = new_content.replace(before2, after2)

        with open(file_path, 'w') as file:
            file.write(new_content)

        print(f"All instances of 'data/config.json' have been replaced in {file_path}.")

if __name__ == '__main__':
    option = int(input("What would you like to do?\n1: Switch code to server mode\n2: Switch code to local mode\n\nOption: "))
    replace_config_path(option)