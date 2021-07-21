import pytest
import allure
import sys
from common import commonFunction
from step import toolbox_steps
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('事件查询')
@pytest.mark.skipif(commonFunction.get_component_health_of_cluster('') is False, reason='')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('events') is False, reason='集群未开启events功能')
class TestEventSearch(object):

    @allure.story('事件总量')
    @allure.title('验证当天的事件总量正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_total_events(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取当前日期的时间戳
        day_timestamp = commonFunction.get_timestamp()
        # 查询当天的事件总量信息
        response = toolbox_steps.step_get_event(day_timestamp, now_timestamp)
        # 获取收集事件的资源数量
        resources_count = response.json()['statistics']['resources']
        # 获取收集到的事件数量
        event_counts = response.json()['statistics']['events']
        # 验证事件数量大于0
        assert resources_count > 0
        # 获取当天的事件趋势图
        interval = '1800'   # 时间间隔,单位是秒
        re = toolbox_steps.step_get_events_trend(day_timestamp, now_timestamp, interval)
        # 获取趋势图的横坐标数量
        count = len(re.json()['histogram']['buckets'])
        # 获取每个时间段的事件数量之和
        events_count_actual = 0
        for i in range(0, count):
            number = re.json()['histogram']['buckets'][i]['count']
            events_count_actual += number
        # 验证接口返回的事件数量和趋势图中的事件之和一致
        assert events_count_actual == event_counts

    @allure.story('事件总量')
    @allure.title('验证最近 12 小时事件总数正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events_12h(self):
        # 时间间隔,单位是秒
        interval = '1800'
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(720)
        # 查询最近 12 小时事件总数变化趋势
        response = toolbox_steps.step_get_events_trend(before_timestamp, now_timestamp, interval)
        # 获取事件总量
        events_count = response.json()['histogram']['total']
        # 获取趋势图的横坐标数量
        count = len(response.json()['histogram']['buckets'])
        # 获取每个时间段的事件数量之和
        events_count_actual = 0
        for i in range(0, count):
            number = response.json()['histogram']['buckets'][i]['count']
            events_count_actual += number
        # 验证接口返回的事件数量和趋势图中的事件之和一致
        assert events_count_actual == events_count

    @allure.story('事件总量')
    @allure.title('查询最近 12 小时事件总数变化趋势')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events_trend(self):
        # 时间间隔,单位是秒
        interval = '1800'
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(720)
        # 查询最近 12 小时事件总数变化趋势
        response = toolbox_steps.step_get_events_trend(before_timestamp, now_timestamp, interval)
        # 获取查询结果数据中的时间间隔
        time_1 = response.json()['histogram']['buckets'][0]['time']
        time_2 = response.json()['histogram']['buckets'][1]['time']
        time_interval = (time_2 - time_1)/1000  # 换算成秒
        # 验证时间间隔正确
        assert time_interval == int(interval)

    @allure.story('事件查询规则')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(('search_rule', 'title'),
                             [('message_search=test', '按消息查询事件趋势'),
                              ('workspace_search=sys', '按企业空间模糊查询事件趋势'),
                              ('workspace_filter=sys', '按企业空间精确查询事件趋势'),
                              ('involved_object_namespace_filter=kube', '按项目精确查询事件趋势'),
                              ('involved_object_namespace_search=kube', '按项目模糊查询事件趋势'),
                              ('involved_object_kind_filter=deployment', '按资源类型查询事件趋势'),
                              ('involved_object_name_filter=kube', '按资源名称精确查询事件趋势'),
                              ('involved_object_name_search=kube', '按资源名称模糊查询事件趋势'),
                              ('reason_filter=Failed', '按原因精确查询事件趋势'),
                              ('reason_search=Failed', '按原因模糊查询事件趋势'),
                              ('type_filter=Warning', '按类别精确查询事件趋势'),
                              ('type_search=Warning', '按类别模糊查询事件趋势'),
                              ('reason_search=Failed', '按原因模糊查询事件趋势')
                              ])
    def test_get_events_trend_by_search(self, search_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按不同条件查询事件
        response = toolbox_steps.step_get_events_trend_by_search(search_rule, now_timestamp)
        # 获取查询结果中的总事件条数
        log_count = response.json()['histogram']['total']
        # 验证查询成功
        assert log_count >= 0

    @allure.story('事件查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('search_rule', 'title'),
                             [('message_search=error', '按消息查询事件趋势'),
                              ('workspace_search=sys', '按企业空间模糊查询事件趋势'),
                              ('workspace_filter=sys', '按企业空间精确查询事件趋势'),
                              ('involved_object_namespace_filter=kube', '按项目精确查询事件趋势'),
                              ('involved_object_namespace_search=kube', '按项目模糊查询事件趋势'),
                              ('involved_object_kind_filter=deployment', '按资源类型查询事件趋势'),
                              ('involved_object_name_filter=kube', '按资源名称精确查询事件趋势'),
                              ('involved_object_name_search=kube', '按资源名称模糊查询事件趋势'),
                              ('reason_filter=Failed', '按原因精确查询事件趋势'),
                              ('reason_search=Failed', '按原因模糊查询事件趋势'),
                              ('type_filter=Warning', '按类别精确查询事件趋势'),
                              ('type_search=Warning', '按类别模糊查询事件趋势'),
                              ('reason_search=Failed', '按原因模糊查询事件趋势')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events_by_search(self, search_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按关键字查询事件详情信息
        response = toolbox_steps.step_get_events_by_search(search_rule, now_timestamp)
        # 获取查询到的事件数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0


