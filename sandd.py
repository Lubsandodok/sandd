from bot import Bot


if __name__ == '__main__':
    bot = Bot()
    success = 0
    for _ in range(1000):
        round, last_fight_monsters = bot.run()
        if round == 20:
            success += 1
            print("win: ", end = ' ')
            print(last_fight_monsters)
        else:
            print("lose: ", end=' ')
            print(last_fight_monsters)
    print(success)
