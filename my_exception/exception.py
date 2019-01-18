
__all__ = ['Data_type_err']

class Data_type_err(Exception):
    def __init__(self, err):
        Exception.__init__(self, err)

#测试
def main():
    i = 1

    try:
        if i == 1:
            raise Data_format_err("this is test err")
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()