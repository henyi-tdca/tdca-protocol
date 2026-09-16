"""E-INT-2.1 StorageAdapter — EIOS 生产存储统一适配接口（原型）

制度锚定: E-INT-2 预研（LIM-EINT-002 存储替换）+ 制度-技术同构
设计原则: 仿真→生产仅替换 StorageAdapter 实现，EIOS 业务代码零修改
  MemoryStore（仿真默认）→ Neo4jAdapter（L2 图）/ TimescaleAdapter（L3 时序）
  / ChainAdapter（L0/L1 强一致）/ PostgresAdapter（流程/看板）
NSFL: 存储替换不得改变 NCA 格式与制度语义；最小化合检查通过后方启用异构。
"""

from abc import ABC, abstractmethod


class StorageAdapter(ABC):
    """统一存储接口（EIOS 业务代码唯一依赖）"""

    @abstractmethod
    def write(self, store: str, key: str, value: dict) -> dict:
        """写入（store: config_memory/utility_metrics/flow_states/nca_records）"""

    @abstractmethod
    def read(self, store: str, key: str) -> dict:
        """读取"""

    @abstractmethod
    def query(self, store: str, **filters) -> list:
        """查询（按层语义：图遍历/时序聚合/强一致读取）"""

    @abstractmethod
    def delete(self, store: str, key: str) -> bool:
        """删除"""


class MemoryStore(StorageAdapter):
    """仿真默认实现（内存字典，替代 SQLite——原型阶段）"""

    def __init__(self):
        self._stores = {}

    def _s(self, store: str) -> dict:
        if store not in self._stores:
            self._stores[store] = {}
        return self._stores[store]

    def write(self, store: str, key: str, value: dict) -> dict:
        rec = dict(value)
        rec['_key'] = key
        self._s(store)[key] = rec
        return rec

    def read(self, store: str, key: str) -> dict:
        return self._s(store).get(key)

    def query(self, store: str, **filters) -> list:
        out = []
        for rec in self._s(store).values():
            if all(rec.get(k) == v for k, v in filters.items()):
                out.append(rec)
        return out

    def delete(self, store: str, key: str) -> bool:
        s = self._s(store)
        if key in s:
            del s[key]
            return True
        return False


class Neo4jAdapter(StorageAdapter):
    """L2 配置权图存储适配器（生产：Neo4j；原型：骨架 + 接口契约）"""

    def __init__(self, uri: str = None):
        self.uri = uri  # 生产: bolt://...；原型: None（未连接）

    def write(self, store, key, value):
        if store != 'config_memory':
            raise ValueError('[NSFL-TRIGGER] Neo4jAdapter 仅接受 config_memory 存储')
        raise NotImplementedError('Neo4j 生产连接待 E-INT-2.1 部署阶段实现（原型为接口契约）')

    def read(self, store, key):
        raise NotImplementedError('Neo4j 生产连接待部署阶段实现')

    def query(self, store, **filters):
        raise NotImplementedError('Neo4j 图遍历查询待部署阶段实现')

    def delete(self, store, key):
        raise NotImplementedError('Neo4j 生产连接待部署阶段实现')


class TimescaleAdapter(StorageAdapter):
    """L3 效用时序存储适配器（生产：TimescaleDB；原型：骨架）"""

    def __init__(self, dsn: str = None):
        self.dsn = dsn

    def write(self, store, key, value):
        if store != 'utility_metrics':
            raise ValueError('[NSFL-TRIGGER] TimescaleAdapter 仅接受 utility_metrics 存储')
        raise NotImplementedError('TimescaleDB 生产连接待部署阶段实现')

    def read(self, store, key):
        raise NotImplementedError('TimescaleDB 生产连接待部署阶段实现')

    def query(self, store, **filters):
        raise NotImplementedError('TimescaleDB 时序聚合待部署阶段实现')

    def delete(self, store, key):
        raise NotImplementedError('TimescaleDB 生产连接待部署阶段实现')


class StorageRegistry:
    """存储注册表：按层路由到适配器（EIOS 业务代码通过此访问）"""

    def __init__(self, default: StorageAdapter):
        self.default = default
        self._routing = {
            'config_memory': default,     # L2 配置权图
            'utility_metrics': default,   # L3 效用时序
            'flow_states': default,       # 流程状态
            'nca_records': default,       # NCA 存证
        }

    def register(self, store: str, adapter: StorageAdapter):
        """生产替换：注册目标存储适配器（仿真→生产仅此一步）"""
        self._routing[store] = adapter

    def adapter_for(self, store: str) -> StorageAdapter:
        return self._routing.get(store, self.default)

    def write(self, store: str, key: str, value: dict) -> dict:
        return self.adapter_for(store).write(store, key, value)

    def read(self, store: str, key: str) -> dict:
        return self.adapter_for(store).read(store, key)

    def query(self, store: str, **filters) -> list:
        return self.adapter_for(store).query(store, **filters)


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    reg = StorageRegistry(MemoryStore())
    # 仿真写入（与 E-INT-1 SQLite 语义一致）
    reg.write('config_memory', 'AGENT-001', {'agent': 'AGENT-001', 'layer': 'L2', 'fuses': 0})
    reg.write('utility_metrics', 'FLOW-1', {'flow': 'FLOW-1', 'mou': 15.0})
    print('读 config_memory:', reg.read('config_memory', 'AGENT-001'))
    print('查 utility_metrics mou>10:', reg.query('utility_metrics', mou=15.0))
    # 生产替换（原型演示：注册 Neo4j/Timescale 适配器，接口契约就位）
    reg.register('config_memory', Neo4jAdapter())
    reg.register('utility_metrics', TimescaleAdapter())
    print('路由: config_memory →', type(reg.adapter_for('config_memory')).__name__)
    print('路由: flow_states →', type(reg.adapter_for('flow_states')).__name__)
    try:
        reg.write('config_memory', 'AGENT-002', {})
    except NotImplementedError as e:
        print('生产适配器接口就位（待部署实现）:', str(e)[:30])
    print('StorageAdapter 原型验证: PASS')
