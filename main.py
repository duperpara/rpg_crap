from character_status import Character


def run(char_json_path):
    char = Character(char_json_path)

    char.use_spell(3)
    char.start_turn()
    char.start_turn()
    # for action_idx in range(len(char.actions)):
    #     char.use_action(action_idx)
    #     char.start_turn()
    # char.use_action(0)
    # char.use_action(0)
    # char.use_action(0)
    input()

if __name__ == '__main__':
    run('./yes.json')
