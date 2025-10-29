from xs128p import predict_sequence


def main():
    browser = 'chrome'
    observed = [
        0.9695987786633904,
        0.28071711843620584,
        0.17303127964472753,
        0.9884694323895107,
        0.5292326613492848,
    ]

    predictions = predict_sequence(observed, 16, browser=browser)

    print('BROWSER: %s' % browser)
    print('Observed sequence:', observed)
    print('Predicted sequence:')
    for value in predictions:
        print(value)


if __name__ == '__main__':
    main()
