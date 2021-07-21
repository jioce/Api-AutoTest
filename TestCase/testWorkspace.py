import requests
import pytest
import json
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header, get_header_for_patch
from common.logFormat import log_format
from common import commonFunction
from step import workspace_steps, platform_step


@allure.feature('企业空间')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestWorkSpace(object):
    user_name = 'user-for-test-ws'
    user_role = 'users-manager'
    ws_name = 'ws-for-test-ws'
    ws_name1 = 'ws1-for-test-ws'
    ws_role_name = ws_name + '-viewer'
    log_format()  # 配置日志格式
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='workspace')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        platform_step.step_create_user(self.user_name, self.user_role)  # 创建一个用户
        workspace_steps.step_create_workspace(self.ws_name)  # 创建一个企业空间
        workspace_steps.step_create_workspace(self.ws_name1)  # 创建一个企业空间,供excle文件中的用例使用
        time.sleep(3)

    def teardown_class(self):
        time.sleep(10)
        workspace_steps.step_delete_workspace(self.ws_name)  # 删除创建的企业空间
        workspace_steps.step_delete_workspace(self.ws_name1)  # 删除供excle中用例使用的企业空间
        platform_step.step_delete_user(self.user_name)  # 删除创建的用户

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,data,story,title,method,severity,condition,except_result', parametrize)
    def test_ws(self, id, url, data, story, title, method, severity, condition, except_result):

        '''
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        '''

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        # test开头的测试函数
        url = config.url + url
        if method == 'get':
            # 测试get方法
            r = requests.get(url, headers=get_header())

        elif method == 'post':
            # 测试post方法
            data = eval(data)
            r = requests.post(url, headers=get_header(), data=json.dumps(data))

        elif method == 'patch':
            # 测试patch方法
            data = eval(data)
            print(data)
            r = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))

        elif method == 'delete':
            # 测试delete方法
            r = requests.delete(url, headers=get_header())

        # 将校验条件和预期结果参数化
        if condition != '':
            condition_new = eval(condition)  # 将字符串转化为表达式
            if isinstance(condition_new, str):
                # 判断表达式的结果是否为字符串，如果为字符串格式，则去掉其首尾的空格
                assert condition_new.strip() == except_result
            else:
                assert condition_new == except_result

            # 将用例中的内容打印在报告中
            print(
                '用例编号: ' + str(id) + '\n'
                                     '用例请求的URL地址: ' + str(url) + '\n'
                                                                 '用例使用的请求数据: ' + str(data) + '\n'
                                                                                             '用例模块: ' + story + '\n'
                                                                                                                '用例标题: ' + title + '\n'
                                                                                                                                   '用例的请求方式: ' + method + '\n'
                                                                                                                                                          '用例优先级: ' + severity + '\n'
                                                                                                                                                                                 '用例的校验条件: ' + str(
                    condition) + '\n'
                                 '用例的实际结果: ' + str(condition_new) + '\n'
                                                                    '用例的预期结果: ' + str(except_result)
            )

    '''
    以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('企业空间设置-企业角色')
    @allure.title('在企业空间编辑角色的权限信息')
    @allure.severity('critical')
    def test_edit_ws_role(self):
        authority_create = '["role-template-view-basic"]'  # 创建角色的权限信息
        authority_edit = '["role-template-view-basic","role-template-create-projects"]'  # 修改目标角色的权限信息
        time.sleep(1)  # 由于新建的角色和系统自动生成的角色的生成时间是一致。后面获取角色的resourceversion是按时间排序获取的。因此在创建企业空间后sleep 1s
        # 在企业空间创建角色
        workspace_steps.step_create_ws_role(self.ws_name, self.ws_role_name, authority_create)
        # 查询并获取该角色的resourceversion
        response = workspace_steps.step_get_ws_role(self.ws_name, self.ws_role_name)
        version = response.json()['items'][0]['metadata']['resourceVersion']
        # 修改角色权限
        workspace_steps.step_edit_role_authory(self.ws_name, self.ws_role_name, version, authority_edit)
        # 查询并获取该角色的权限信息
        re = workspace_steps.step_get_ws_role(self.ws_name, self.ws_role_name)
        authority_actual = re.json()['items'][0]['metadata']['annotations']["iam.kubesphere.io/aggregation-roles"]
        # 验证修改角色权限后的权限信息
        assert authority_actual == authority_edit
        # 删除创建的角色
        workspace_steps.step_delete_role(self.ws_name, self.ws_role_name)

    @allure.story('企业空间设置-企业成员')
    @allure.title('在企业空间邀请存在的新成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_invite_user(self):
        # 创建用户
        user_name = 'user' + str(commonFunction.get_random())
        user_role = 'users-manager'
        platform_step.step_create_user(user_name, user_role)
        # 创建角色
        authority_create = '["role-template-view-basic"]'  # 创建角色的权限信息
        role_name = 'role' + str(commonFunction.get_random())
        workspace_steps.step_create_ws_role(self.ws_name, role_name, authority_create)
        # 将用户邀请到企业空间
        r1 = workspace_steps.step_invite_user(self.ws_name, user_name, role_name)
        # 在企业空间中查询邀请的用户
        response = workspace_steps.step_get_ws_user(self.ws_name, user_name)
        # 验证邀请后的成员名称
        assert response.json()['items'][0]['metadata']['name'] == user_name
        # 将邀请的用户移除企业空间
        workspace_steps.step_delete_ws_user(self.ws_name, user_name)
        # 删除创建的用户
        platform_step.step_delete_user(user_name)

    @allure.story('企业空间设置-企业角色')
    @allure.title('在企业空间编辑邀请成员的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_edit_invite_user(self):
        # 创建用户
        user_name = 'user' + str(commonFunction.get_random())
        user_role = 'users-manager'
        platform_step.step_create_user(user_name, user_role)
        ws_role_create = self.ws_name + '-viewer'  # 邀请用户是赋予的角色
        ws_role_new = self.ws_name + '-admin'  # 修改的新角色
        # 将创建的用户邀请到创建的企业空间
        workspace_steps.step_invite_user(self.ws_name, user_name, ws_role_create)
        # 修改成员角色
        workspace_steps.step_edit_ws_user_role(self.ws_name, user_name, ws_role_new)
        # 查询该企业空间成员的信息
        r = workspace_steps.step_get_ws_user(self.ws_name, user_name)
        # 获取该成员的角色信息
        user_role = r.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/workspacerole']
        # 验证修改后的角色名称
        assert user_role == ws_role_new
        # 将邀请的用户移除企业空间
        workspace_steps.step_delete_ws_user(self.ws_name, user_name)
        # 删除创建的用户
        platform_step.step_delete_user(user_name)

    @allure.story('企业空间设置-企业成员')
    @allure.title('在企业空间删除邀请的成员并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_delete_invite_user(self):
        # 创建用户
        user_name = 'user' + str(commonFunction.get_random())
        user_role = 'users-manager'
        platform_step.step_create_user(user_name, user_role)
        ws_role_create = self.ws_name + '-viewer'  # 邀请用户是赋予的角色
        # 将创建的用户邀请到创建的企业空间
        workspace_steps.step_invite_user(self.ws_name, user_name, ws_role_create)
        # 将邀请的用户移除企业空间
        workspace_steps.step_delete_ws_user(self.ws_name, user_name)
        # 查询该企业空间成员的信息
        response = workspace_steps.step_get_ws_user(self.ws_name, user_name)
        # 验证移除用户成功
        assert response.json()['totalItems'] == 0
        # 删除创建的用户
        platform_step.step_delete_user(user_name)

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建、编辑、删除企业组织')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_department(self):
        group_name = 'test-group'
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 创建企业组织,并获取创建的企业组织的name
        response = workspace_steps.step_create_department(self.ws_name, group_name, data)
        name = response.json()['metadata']['name']
        # 获取所有的企业组织名称
        group_name_actual = workspace_steps.step_get_department(self.ws_name)
        # 校验企业组织名称，已验证企业组织创建成功
        assert group_name in group_name_actual
        # 编辑企业组织
        edit_data = {"metadata": {"annotations": {"kubesphere.io/workspace-role": "wx-regular",
                                                  "kubesphere.io/alias-name": "我是别名",
                                                  "kubesphere.io/project-roles": "[]",
                                                  "kubesphere.io/devops-roles": "[]",
                                                  "kubesphere.io/creator": "admin"}}}
        annotations = workspace_steps.step_edit_department(self.ws_name, name, edit_data)
        # 验证编辑后的内容
        assert "我是别名" == annotations['kubesphere.io/alias-name']
        # 删除企业组织,并获取返回信息
        response = workspace_steps.step_delete_department(self.ws_name, name)
        # 验证删除成功
        assert response.json()['message'] == 'success'

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建重名的企业组织')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_rename_department(self):
        # 创建企业组织
        group_name = 'test-group'
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 创建企业组织,并获取创建的企业组织的name
        response = workspace_steps.step_create_department(self.ws_name, group_name, data)
        name = response.json()['metadata']['name']
        # 创建一个同名的企业组织
        respon = workspace_steps.step_create_department(self.ws_name, group_name, data)
        # 校验接口返回信息
        assert_message = 'Operation cannot be fulfilled on groups.iam.kubesphere.io "' + \
                         group_name + '": a group named ' + group_name + ' already exists in the workspace\n'
        assert respon.text == assert_message
        # 删除创建的企业空间
        res = workspace_steps.step_delete_department(self.ws_name, name)
        # 验证删除成功
        res.json()['message'] == 'success'

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建的企业组织名称中包含大写字母')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_wrong_name_department(self):
        # 创建组织
        group_name = 'Test-group'
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 获取返回信息
        response = workspace_steps.step_create_department(self.ws_name, group_name, data)
        assert_message = 'is invalid: [metadata.generateName: Invalid value: "' + group_name + '"'
        # 校验接口返回信息
        assert assert_message in response.text

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建的企业组织名称中包含特殊字符')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_wrong_name_1_department(self):
        # 创建组织
        group_name = '@est-group'
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 获取返回信息
        response = workspace_steps.step_create_department(self.ws_name, group_name, data)
        assert_message = 'is invalid: [metadata.generateName: Invalid value: "' + group_name + '"'
        # 校验接口返回信息
        assert assert_message in response.text

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建企业组织时绑定不存在的项目')
    # 接口没有校验企业空间的角色、项目和角色是否存在
    def wx_test_create_wrong_pro_department(self):
        group_name = 'test-group'
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[{\"cluster\":\"\",\"namespace\":\"test\",\"role\":\"viewer1\"}]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 获取返回信息
        response = workspace_steps.step_create_department(self.ws_name, group_name, data)
        print(response.text)

    @allure.story('企业空间设置-企业组织')
    @allure.title('为用户分配企业组织')
    def test_assign_user(self):
        # 创建用户
        user_name = 'user' + str(commonFunction.get_random())
        user_role = 'users-manager'
        platform_step.step_create_user(user_name, user_role)
        # 将用户邀请到企业空间
        workspace_steps.step_invite_user(self.ws_name, user_name, self.ws_name + '-viewer')
        # 创建企业组织
        group_name = 'group' + str(commonFunction.get_random())
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 创建企业组织,并获取创建的企业组织的name
        response = workspace_steps.step_create_department(self.ws_name, group_name, data)
        name = response.json()['metadata']['name']
        # 获取该企业组织可分配的用户数量
        res = workspace_steps.step_get_user_for_department(name)
        counts = res.json()['totalItems']
        # 将指定用户绑定到指定企业组织
        re = workspace_steps.step_binding_user(self.ws_name, name, user_name)
        # 获取绑定后返回的用户名
        binding_user = re.json()[0]['users'][0]
        # 校验绑定的用户名称
        assert binding_user == user_name
        # 重新获取企业组织可分配的用户数量
        r = workspace_steps.step_get_user_for_department(name)
        counts_new = r.json()['totalItems']
        # 验证可绑定的用户数量
        assert counts_new == counts - 1
        #删除创建的用户
        platform_step.step_delete_user(user_name)

    @allure.story('企业空间设置-企业组织')
    @allure.title('将已绑定企业组织的用户再次绑定该企业组织')
    # 接口没有限制将同一个用户重复绑定到一个企业组织
    def wx_test_reassign_user(self):
        group_name = 'test2'
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 创建企业组织,并获取创建的企业组织的name
        response = workspace_steps.step_create_department(self.ws_name, group_name, data)
        name = response.json()['metadata']['name']
        # 将指定用户绑定到指定企业组织
        workspace_steps.step_binding_user(self.ws_name, name, self.user_name)
        # 将指定用户再次绑定到该企业空间
        response = workspace_steps.step_binding_user(self.ws_name, name, self.user_name)
        print(response.text)

    @allure.story('企业空间设置-企业组织')
    @allure.title('将用户从企业组织解绑')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_unbind_user(self):
        # 创建用户
        user_name = 'user' + str(commonFunction.get_random())
        user_role = 'users-manager'
        platform_step.step_create_user(user_name, user_role)
        group_name = 'group' + str(commonFunction.get_random())
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 创建企业组织,并获取创建的企业组织的name
        response = workspace_steps.step_create_department(self.ws_name, group_name, data)
        name = response.json()['metadata']['name']
        # 将指定用户绑定到指定企业组织
        res = workspace_steps.step_binding_user(self.ws_name, name, user_name)
        # 获取绑定后返回的用户名
        binding_user = res.json()[0]['metadata']['name']
        # 将用户从企业组织解绑
        response = workspace_steps.step_unbind_user(ws_name=self.ws_name, user_name=binding_user)
        # 校验解绑结果
        assert response.json()['message'] == 'success'
        # 删除创建的用户
        platform_step.step_delete_user(user_name)
        # 删除创建的企业组织
        workspace_steps.step_delete_department(self.ws_name, group_name)

    @allure.story('企业空间设置-配额管理')
    @allure.title('编辑配额')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_quota(self):
        # 初始化企业配额
        workspace_steps.step_init_quota(ws_name=self.ws_name, cluster='default')
        # 获取企业配额的resourceVersion
        res = workspace_steps.step_get_quota_resource_version(self.ws_name)
        resource_version = res.json()['metadata']['resourceVersion']
        # 编辑企业配额
        hard_data = {"limits.cpu": "100", "limits.memory": "100Gi",
                     "requests.cpu": "1", "requests.memory": "1Gi"}
        response = workspace_steps.step_edit_quota(ws_name=self.ws_name, hard_data=hard_data, cluster='default',
                                   resource_version=resource_version)
        # 获取返回的配额信息
        hard_info = response.json()['spec']['quota']['hard']
        # 校验修改后的配额信息
        assert hard_data == hard_info

    @allure.story('配额管理')
    @allure.title('编辑配额是的request.cpu > limit.cpu')
    # 接口没有限制limit >= request
    def wx_test_edit_quota_cpu(self):
        # 初始化企业配额
        workspace_steps.step_init_quota(ws_name=self.ws_name, cluster='default')
        # 获取企业配额的resourceVersion
        res = workspace_steps.step_get_quota_resource_version(self.ws_name)
        resource_version = res.json()['metadata']['resourceVersion']
        # 编辑企业配额
        hard_data = {"limits.cpu": "1", "limits.memory": "100Gi",
                     "requests.cpu": "2", "requests.memory": "1Gi"}
        response = workspace_steps.step_edit_quota(ws_name=self.ws_name, hard_data=hard_data, cluster='default',
                                   resource_version=resource_version)
        print(response.text)

    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('network') is False,
                        reason='集群未开启networkpolicy功能')
    @allure.story('企业空间设置-网络策略')
    @allure.title('关闭企业空间网络隔离')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_off_network_lsolation(self):
        # 关闭企业空间网络隔离
        workspace_steps.step_set_network_lsolation(self.ws_name, False)
        # 验证企业空间信息
        response = workspace_steps.step_get_ws_info(self.ws_name)
        # 获取企业空间的网络隔离状态
        network_lsolation = response.json()['spec']['template']['spec']['networkIsolation']
        # 验证设置成功
        assert network_lsolation is False

    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('network') is False,
                        reason='集群未开启networkpolicy功能')
    @allure.story('企业空间设置-网络策略')
    @allure.title('开启企业空间网络隔离')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_enable_network_lsolation(self):
        # 关闭企业空间网络隔离
        workspace_steps.step_set_network_lsolation(self.ws_name, True)
        # 验证企业空间信息
        response = workspace_steps.step_get_ws_info(self.ws_name)
        # 获取企业空间的网络隔离状态
        network_lsolation = response.json()['spec']['template']['spec']['networkIsolation']
        # 验证设置成功
        assert network_lsolation is True


if __name__ == "__main__":
    pytest.main(['-s', 'testWorkspace.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
