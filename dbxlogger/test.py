
class B:
    def __init__(self):
        print("inited B")

    def close(self):
        print("closed b")

class F:
    def __init__(self):
        print("called init")

    def __enter__(self):
        print('called enter')
        self.b = B()
        return self.b

    def __exit__(self, *args, **kwargs):
        print("called exit args=%s, kwargs=%s" % (str(args), str(kwargs)))
        self.b.close()
