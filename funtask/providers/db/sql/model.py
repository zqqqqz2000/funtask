from enum import auto, unique
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, VARBINARY, Boolean, Float, BigInteger, JSON, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship

from funtask.utils.enum_utils import AutoName

Base = declarative_base()


@unique
class ParentTaskType(AutoName):
    TASK = auto()
    CRON_TASK = auto()


@unique
class WorkerStatus(AutoName):
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    DIED = auto()


@unique
class TaskStatus(AutoName):
    UNSCHEDULED = auto()
    SCHEDULED = auto()
    SKIP = auto()
    QUEUED = auto()
    RUNNING = auto()
    SUCCESS = auto()
    ERROR = auto()
    DIED = auto()


class Worker(Base):
    __tablename__ = 'worker'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(String(36), nullable=False)
    status = Column(Enum(WorkerStatus), nullable=False)
    name = Column(String(64), nullable=True)
    last_heart_beat = Column(TIMESTAMP(), nullable=False)


class ParameterSchema(Base):
    __tablename__ = 'parameter_schema'
    id = Column(Integer(), primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(String(36), nullable=False)
    functions: 'List[Function]'


class Function(Base):
    __tablename = 'function'
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(String(36), nullable=False)
    parameter_schema_id = Column(Integer(), ForeignKey('parameter_schema.id'), nullable=True)
    parameter_schema: ParameterSchema | None = relationship('ParameterSchema', backref='functions')
    function = Column(VARBINARY(1024), nullable=False)
    name = Column(String(64), nullable=True)
    ref_tasks: 'List[Task]'
    ref_cron_tasks: 'List[CronTask]'


class Task(Base):
    __tablename__ = 'task'
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(String(36), nullable=False)
    uuid_in_manager = Column(String(36), nullable=False)
    parent_task = Column(String(36), nullable=True)
    parent_task_type = Column(Enum(ParentTaskType), nullable=True)
    worker_id = Column(BigInteger(), ForeignKey('worker.id'), nullable=True)
    worker: Worker = relationship('Worker')
    status = Column(Enum(TaskStatus), nullable=False)
    func_id = Column(BigInteger(), ForeignKey('functions.id'), nullable=False)
    func: Function = relationship('Function', backref="ref_tasks")
    argument = Column(VARBINARY(1024), nullable=False)
    result_as_state = Column(Boolean(), nullable=False)
    timeout = Column(Float(), nullable=True)
    description = Column(String(256), nullable=True)
    result = Column(String(1024), nullable=False)


@unique
class ArgumentStrategy(AutoName):
    STATIC = auto()
    DROP = auto()
    SKIP = auto()
    FROM_QUEUE_END_REPEAT_LATEST = auto()
    FROM_QUEUE_END_SKIP = auto()
    FROM_QUEUE_END_DROP = auto()
    UDF = auto()


class Queue(AutoName):
    __tablename__ = 'queue'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(String(36), nullable=False)
    name = Column(String(64), nullable=False)


@unique
class WorkerChooseStrategy(AutoName):
    STATIC = auto()
    RANDOM_FROM_LIST = auto()
    RANDOM_FROM_WORKER_TAGS = auto()
    UDF = auto()


@unique
class QueueFullStrategy(AutoName):
    SKIP = auto()
    DROP = auto()
    SEIZE = auto()
    UDF = auto()


@unique
class TagType(AutoName):
    CronTask = auto()
    Worker = auto()
    function = auto()


class Tag(Base):
    __tablename__ = 'tag'
    tag = Column(String(32), nullable=False)
    related_uuid = Column(String(36), nullable=False)
    tag_type = Column(Enum(TagType), nullable=False)


class CronTask(Base):
    __tablename__ = 'cron_task'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(String(36), nullable=False)
    name = Column(String(64), nullable=False)
    function_id = Column(BigInteger(), ForeignKey('functions.id'), nullable=False)
    argument_generate_strategy = Column(Enum(ArgumentStrategy), nullable=False)
    argument_generate_strategy_static_value = Column(VARBINARY(1024), nullable=True)
    argument_generate_strategy_args_queue = Column(String(36), ForeignKey('queue.id'), nullable=True)
    argument_generate_strategy_udf = Column(String(36), ForeignKey('function.id'), nullable=True)
    argument_generate_strategy_udf_extra = Column(VARBINARY(1024), nullable=True)
    worker_choose_strategy = Column(Enum(WorkerChooseStrategy), nullable=False)
    worker_choose_strategy_static_worker = Column(String(36), ForeignKey('worker.uuid'), nullable=True)
    worker_choose_strategy_worker_list = Column(JSON(none_as_null=False), nullable=True)
    worker_choose_strategy_worker_tags = Column(JSON(none_as_null=False), nullable=True)
    worker_choose_strategy_udf = Column(String(36), ForeignKey('function.id'), nullable=True)
    worker_choose_strategy_udf_extra = Column(VARBINARY(1024), nullable=True)
    task_queue_strategy = Column(Enum(QueueFullStrategy), nullable=False)
    task_queue_max_size = Column(BigInteger(), nullable=False)
    task_queue_strategy_udf = Column(String(36), ForeignKey('function.id'), nullable=True)
    task_queue_strategy_udf_extra = Column(VARBINARY(1024), nullable=True)
    result_as_status = Column(Boolean(), nullable=False)
    timeout = Column(Float(), nullable=True)
    description = Column(String(256), nullable=True)
    disabled = Column(Boolean(), nullable=False)
    func: Function = relationship('Function', backref="ref_corn_tasks")
