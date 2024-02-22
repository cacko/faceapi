from queue import Queue

class QueueMeta(type):
    
    __instances: dict[str, Queue] = {}
    
    def __call__(cls, *args, **kwds):
        k = cls.__name__
        if k not in cls.__instances:
            cls.__instances[k] = type.__call__(cls, *args, **kwds)
        return cls.__instances[k]
        

class GeneratorQueue(Queue, metaclass=QueueMeta):
    pass