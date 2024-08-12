from bot import Bot


if __name__ == '__main__':
    bot = Bot()
    success = 0
    for _ in range(10000):
        round = bot.run()
        if round == 20:
            success += 1
    print(success)
