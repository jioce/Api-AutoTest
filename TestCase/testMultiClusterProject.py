# -- coding: utf-8 --
import pytest
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common import commonFunction
from step import project_steps, cluster_steps, workspace_steps, platform_steps


@allure.feature('多集群项目管理')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='未开启多集群功能,单集群环境下不执行')
class TestProject(object):
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = commonFunction.check_multi_cluster()

    volume_name = 'testvolume'  # 存储卷名称，在创建、删除存储卷和创建存储卷快照时使用,excle中的用例也用到了这个存储卷
    snapshot_name = 'testshot'  # 存储卷快照的名称,在创建和删除存储卷快照时使用，在excle中的用例也用到了这个快照
    user_name = 'user-for-test-project' + str(commonFunction.get_random())  # 系统用户名称
    user_role = 'workspaces-manager'
    ws_name = 'ws-for-test-project'
    ws_name_actual = ws_name + str(commonFunction.get_random())
    alias_name = '多集群'
    description = '用于测试多集群项目管理'
    project_name = 'test-project' + str(commonFunction.get_random())
    ws_role_name = ws_name + '-viewer'  # 企业空间角色名称
    project_role_name = 'test-project-role'  # 项目角色名称
    job_name = 'demo-job'  # 任务名称,在创建和删除任务时使用
    work_name = 'workload-demo'  # 工作负载名称，在创建、编辑、删除工作负载时使用

    # 所有用例执行之前执行该方法
    def setup_class(self):
        platform_steps.step_create_user(self.user_name, self.user_role)  # 创建一个用户
        # 获取集群名称
        clusters = cluster_steps.step_get_cluster_name()
        # 创建一个多集群企业空间（包含所有的集群）
        workspace_steps.step_create_multi_ws(self.ws_name_actual,
                                             self.alias_name, self.description, clusters)
        # 创建若干个多集群企业空间（只部署在单个集群）
        if len(clusters) > 1:
            for i in range(0, len(clusters)):
                workspace_steps.step_create_multi_ws(self.ws_name_actual, self.alias_name,
                                                     self.description, clusters[i])
        # 在每个企业空间创建多集群项目,且将其部署在所有和单个集群上
        response = workspace_steps.step_get_ws_info(self.ws_name)
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            # 获取企业空间的集群信息
            clusters_name = []
            re = workspace_steps.step_get_ws_info(ws_name)
            clusters = re.json()['items'][0]['spec']['placement']['clusters']
            for i in range(0, len(clusters)):
                clusters_name.append(clusters[i]['name'])
            if len(clusters_name) > 1:
                # 创建多集群项目,但是项目部署在单个集群上
                for j in range(0, len(clusters_name)):
                    multi_project_name = 'multi-pro' + str(commonFunction.get_random())
                    project_steps.step_create_multi_project(ws_name, multi_project_name, clusters_name[j])
            else:
                multi_project_name = 'multi-pro' + str(commonFunction.get_random())
                project_steps.step_create_multi_project(ws_name, multi_project_name, clusters_name)

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        # 获取环境中所有的多集群项目
        multi_project_name = project_steps.step_get_multi_projects_name()
        for multi_project in multi_project_name:
            if 'multi-pro' in multi_project:
                # 删除创建的多集群项目
                project_steps.step_delete_project_by_name(multi_project)
        time.sleep(5)
        # 获取环境中所有的企业空间
        response = workspace_steps.step_get_ws_info(self.ws_name)
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            # 获取企业空间的集群信息
            if ws_name != 'system-workspace':
                commonFunction.delete_workspace(ws_name)  # 删除创建的工作空间
        # 删除创建的用户
        platform_steps.step_delete_user(self.user_name)

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_deployment(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            type_name = 'volume-type'  # 存储卷的类型
            work_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            volume_name = 'volume-deploy' + str(commonFunction.get_random())  # 存储卷名称
            replicas = 1  # 副本数
            image = 'redis'  # 镜像名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + work_name  # 查询条件
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
            volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
            # 创建存储卷
            project_steps.step_create_volume_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0], volume_name=volume_name)
            # 创建资源并将存储卷绑定到资源
            project_steps.step_create_deploy_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0], work_name=work_name,
                                                              image=image, replicas=replicas,
                                                              container_name=container_name,
                                                              volume_info=volume_info, ports=port,
                                                              volumemount=volumeMounts, strategy=strategy_info)

            i = 0
            while i < 100:
                # 获取工作负载的状态
                response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                            project_name=project_info[0],
                                                                            type='deployments', condition=condition)
                try:
                    readyReplicas = response.json()['items'][0]['status']['readyReplicas']
                    if readyReplicas:
                        break
                    else:
                        time.sleep(5)
                        i += 5
                except Exception as e:
                    print(e)
            # 验证资源的所有副本已就绪
            assert readyReplicas == replicas
            # 获取存储卷状态
            re = project_steps.step_get_volume_status_in_multi_project(cluster_name=project_info[1],
                                                                       project_name=project_info[0],
                                                                       volume_name=volume_name)
            status = re.json()['items'][0]['status']['phase']
            # 验证存储卷状态正常
            assert status == 'Bound'
            # 删除工作负载
            project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type='deployments',
                                                                work_name=work_name)
            # 删除存储卷
            project_steps.step_delete_volume_in_multi_project(project_info[0], volume_name)

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的statefulsets上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_statefulsets(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            volume_name = 'volume-stateful' + str(commonFunction.get_random())  # 存储卷的名称
            type_name = 'volume-type'  # 存储卷的类型
            work_name = 'stateful' + str(commonFunction.get_random())  # 工作负载的名称
            service_name = 'service' + volume_name  # 服务名称
            replicas = 2  # 副本数
            image = 'nginx'  # 镜像名称
            container_name = 'container-stateful' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + work_name  # 查询条件
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
            service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
            volumemounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]
            volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
            # 创建存储卷
            project_steps.step_create_volume_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0], volume_name=volume_name)
            # 创建资源并将存储卷绑定到资源
            project_steps.step_create_stateful_in_multi_project(cluster_name=project_info[1],
                                                                project_name=project_info[0], work_name=work_name,
                                                                container_name=container_name, image=image,
                                                                replicas=replicas,
                                                                ports=port, service_ports=service_port,
                                                                volumemount=volumemounts, volume_info=volume_info,
                                                                service_name=service_name)
            # 验证资源创建成功
            i = 0
            while i < 100:
                # 获取工作负载的状态
                try:
                    response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                                project_name=project_info[0],
                                                                                type='statefulsets', condition=condition)
                    readyReplicas = response.json()['items'][0]['status']['readyReplicas']
                    if readyReplicas == replicas:
                        break
                    else:
                        i += 5
                        time.sleep(5)
                except Exception as e:
                    print(e)
            # 获取存储卷状态
            response = project_steps.step_get_volume_status_in_multi_project(cluster_name=project_info[1],
                                                                             project_name=project_info[0],
                                                                             volume_name=volume_name)
            status = response.json()['items'][0]['status']['phase']
            # 验证存储卷状态正常
            assert status == 'Bound'
            # 删除工作负载
            project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type='deployments',
                                                                work_name=work_name)
            # 删除存储卷
            project_steps.step_delete_volume_in_multi_project(project_info[0], volume_name)

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的service上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_service(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            volume_name = 'volume-service' + str(commonFunction.get_random())  # 存储卷的名称
            type_name = 'volume-type'  # 存储卷的类型
            service_name = 'service' + str(commonFunction.get_random())  # 工作负载的名称
            image = 'redis'  # 镜像名称
            container_name = 'container-daemon' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + service_name  # 查询条件
            port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
            port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
            volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
            volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            # 创建存储卷
            project_steps.step_create_volume_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0], volume_name=volume_name)
            # 创建service
            project_steps.step_create_service_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0],
                                                               service_name=service_name, port=port_service)
            # 创建service绑定的deployment
            project_steps.step_create_deploy_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0],
                                                              work_name=service_name, container_name=container_name,
                                                              ports=port_deploy, volumemount=volumeMounts, image=image,
                                                              replicas=replicas,
                                                              volume_info=volume_info, strategy=strategy_info)
            i = 0
            while i < 100:
                # 获取工作负载的状态
                try:
                    response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                                project_name=project_info[0],
                                                                                type='deployments',
                                                                                condition=condition)
                    readyReplicas = response.json()['items'][0]['status']['readyReplicas']
                    if readyReplicas == replicas:
                        break
                    else:
                        i += 5
                        time.sleep(5)
                except Exception as e:
                    print(e)
            # 获取存储卷状态
            response = project_steps.step_get_volume_status_in_multi_project(cluster_name=project_info[1],
                                                                             project_name=project_info[0],
                                                                             volume_name=volume_name)
            status = response.json()['items'][0]['status']['phase']
            # 验证存储卷状态正常
            assert status == 'Bound'
            # 删除service
            project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type='services',
                                                                work_name=service_name)
            # 删除deployment
            project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type='deployments',
                                                                work_name=service_name)
            # 删除存储卷
            project_steps.step_delete_volume_in_multi_project(project_info[0], volume_name)

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目创建未绑定存储卷的deployment，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_deployment(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            condition = 'name=' + workload_name  # 查询条件
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 1  # 副本数
            volume_info = []
            # 创建工作负载
            project_steps.step_create_deploy_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0], work_name=workload_name,
                                                              container_name=container_name, ports=port,
                                                              volumemount=volumeMounts,
                                                              image=image, replicas=replicas, volume_info=volume_info,
                                                              strategy=strategy_info)

            # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
            i = 0
            while i < 60:
                response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                            project_name=project_info[0],
                                                                            type='deployments', condition=condition)
                try:
                    status = response.json()['items'][0]['status']
                except Exception as e:
                    print(e)
                # 验证资源的所有副本已就绪
                if 'unavailableReplicas' not in status:
                    print('创建工作负载耗时:' + str(i) + 's')
                    break
                time.sleep(1)
                i = i + 1
            assert 'unavailableReplicas' not in status
            # 删除deployment
            re = project_steps.step_delete_workload_in_multi_project(project_name=project_info[0],
                                                                     type='deployments', work_name=workload_name)
            assert re.json()['status']['conditions'][0]['status'] == 'True'

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目按名称查询存在的deployment')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_deployment_by_name(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            conndition = 'name=' + workload_name  # 查询条件
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载哦的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建工作负载
            project_steps.step_create_deploy_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0], work_name=workload_name,
                                                              container_name=container_name, ports=port,
                                                              volumemount=volumeMounts,
                                                              image=image, replicas=replicas, volume_info=volume_info,
                                                              strategy=strategy_info)
            time.sleep(3)
            # 按名称精确查询deployment
            response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                        project_name=project_info[0],
                                                                        type='deployments', condition=conndition)
            # 获取并验证deployment的名称正确
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
            assert name == workload_name
            # 删除deployment
            re = project_steps.step_delete_workload_in_multi_project(project_name=project_info[0],
                                                                     type='deployments', work_name=workload_name)
            assert re.json()['status']['conditions'][0]['status'] == 'True'

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目创建未绑定存储卷的StatefulSets，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_statefulsets(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            replicas = 2  # 副本数
            condition = 'name=' + workload_name  # 查询条件
            volume_info = []
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
            service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
            service_name = 'service' + workload_name
            volumemounts = []
            # 创建工作负载
            project_steps.step_create_stateful_in_multi_project(cluster_name=project_info[1],
                                                                project_name=project_info[0], work_name=workload_name,
                                                                container_name=container_name,
                                                                image=image, replicas=replicas, volume_info=volume_info,
                                                                ports=port,
                                                                service_ports=service_port, volumemount=volumemounts,
                                                                service_name=service_name)
            # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
            i = 0
            while i < 60:
                try:
                    response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                                project_name=project_info[0],
                                                                                type='statefulsets', condition=condition)
                    readyReplicas = response.json()['items'][0]['status']['readyReplicas']
                    # 验证资源的所有副本已就绪
                    if readyReplicas == replicas:
                        print('创建工作负载耗时:' + str(i) + 's')
                        break
                    time.sleep(3)
                    i = i + 3
                except Exception as e:
                    print(e)
            assert readyReplicas == replicas
            # 删除创建的工作负载
            project_steps.step_delete_workload_in_multi_project(project_name=project_info[0],
                                                                type='services', work_name=workload_name)
            re = project_steps.step_delete_workload_in_multi_project(project_name=project_info[0],
                                                                     type='statefulsets', work_name=workload_name)
            assert re.json()['status']['conditions'][0]['status'] == 'True'

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目按名称查询存在的StatefulSets')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_statefulstes_by_name(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            condition = 'name=' + workload_name
            type = 'statefulsets'
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            replicas = 2  # 副本数
            volume_info = []
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
            service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
            service_name = 'service' + workload_name
            volumemounts = []
            # 创建工作负载
            project_steps.step_create_stateful_in_multi_project(cluster_name=project_info[1],
                                                                project_name=project_info[0], work_name=workload_name,
                                                                container_name=container_name,
                                                                image=image, replicas=replicas, volume_info=volume_info,
                                                                ports=port,
                                                                service_ports=service_port, volumemount=volumemounts,
                                                                service_name=service_name)

            # 按名称精确查询statefulsets
            time.sleep(1)
            response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                        project_name=project_info[0],
                                                                        type=type, condition=condition)
            # 获取并验证statefulsets的名称正确
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除创建的工作负载
                project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type=type,
                                                                    work_name=workload_name)
                pytest.xfail('工作负载创建失败，标记为xfail')
                break
            assert name == workload_name
            # 删除创建的statefulsets
            re = project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type=type,
                                                                     work_name=workload_name)
            assert re.json()['status']['conditions'][0]['status'] == 'True'

    @allure.story('应用负载-服务')
    @allure.title('创建未绑定存储卷的service，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_service(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            service_name = 'service' + str(commonFunction.get_random())  # 服务名称
            port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
            image = 'nginx'  # 镜像名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + service_name  # 查询deploy和service条件
            port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建service
            project_steps.step_create_service_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0],
                                                               service_name=service_name, port=port_service)
            # 创建service绑定的deployment
            project_steps.step_create_deploy_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0],
                                                              work_name=service_name, container_name=container_name,
                                                              ports=port_deploy, volumemount=volumeMounts, image=image,
                                                              replicas=replicas,
                                                              volume_info=volume_info, strategy=strategy_info)
            # 验证service创建成功
            response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                        project_name=project_info[0],
                                                                        type='services', condition=condition)
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除创建的工作负载
                project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type='services',
                                                                    work_name=service_name)
                pytest.xfail('服务创建失败，标记为xfail')
                break
            assert name == service_name
            # 验证deploy创建成功
            time.sleep(3)
            re = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                  project_name=project_info[0],
                                                                  type='deployments', condition=condition)
            # 获取并验证deployment的名称正确
            name = re.json()['items'][0]['metadata']['name']
            assert name == service_name
            # 删除service
            project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type='services',
                                                                work_name=service_name)
            # 删除deployment
            project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type='deployments',
                                                                work_name=service_name)

    @allure.story('应用负载-服务')
    @allure.title('在多集群项目删除service，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_service(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            service_name = 'service' + str(commonFunction.get_random())
            port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
            condition = 'name=' + service_name  # 查询service的条件
            # 创建service
            project_steps.step_create_service_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0],
                                                               service_name=service_name, port=port_service)
            i = 0
            while i < 100:
                try:
                    # 验证service创建成功
                    response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                                project_name=project_info[0],
                                                                                type='services', condition=condition)
                    name = response.json()['items'][0]['metadata']['name']
                    if name:
                        break
                    else:
                        time.sleep(3)
                        i += 3
                except Exception as e:
                    print(e)
            assert name == service_name
            # 删除service
            project_steps.step_delete_workload_in_multi_project(project_info[0], 'services', service_name)
            time.sleep(10)  # 等待删除成功
            # 验证service删除成功
            response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                        project_name=project_info[0],
                                                                        type='services', condition=condition)
            count = response.json()['totalItems']
            assert count == 0

    @allure.story('应用负载-应用路由')
    @allure.title('在多集群项目为服务创建应用路由')
    def test_create_route(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 创建服务
            service_name = 'service' + str(commonFunction.get_random())  # 服务名称
            port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
            image = 'nginx'  # 镜像名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + service_name  # 查询deploy和service条件
            port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建service
            project_steps.step_create_service_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0],
                                                               service_name=service_name, port=port_service)
            # 创建service绑定的deployment
            project_steps.step_create_deploy_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0],
                                                              work_name=service_name, container_name=container_name,
                                                              ports=port_deploy, volumemount=volumeMounts, image=image,
                                                              replicas=replicas,
                                                              volume_info=volume_info, strategy=strategy_info)
            # 验证service创建成功
            response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                        project_name=project_info[0],
                                                                        type='services', condition=condition)
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除创建的工作负载
                project_steps.step_delete_workload_in_multi_project(project_name=project_info[0], type='services',
                                                                    work_name=service_name)
                pytest.xfail('服务创建失败，标记为xfail')
                break
            assert name == service_name
            # 验证deploy创建成功
            time.sleep(3)
            re = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                  project_name=project_info[0],
                                                                  type='deployments', condition=condition)
            # 获取并验证deployment的名称正确
            name = re.json()['items'][0]['metadata']['name']
            assert name == service_name
            # 为服务创建路由
            ingress_name = 'ingress' + str(commonFunction.get_random())
            host = 'www.test' + str(commonFunction.get_random()) + '.com'
            service_info = {"serviceName": service_name, "servicePort": 80}
            response = project_steps.step_create_route_in_multi_project(cluster_name=project_info[1],
                                                                        project_name=project_info[0],
                                                                        ingress_name=ingress_name, host=host,
                                                                        service_info=service_info)
            # 获取路由绑定的服务名称
            name = \
                response.json()['spec']['overrides'][0]['clusterOverrides'][0]['value'][0]['http']['paths'][0][
                    'backend'][
                    'serviceName']
            # 验证路由创建成功
            assert name == service_name

    @allure.story('项目设置-高级设置')
    @allure.title('在多集群项目设置网关-NodePort')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_gateway_nodeport(self):
        type = 'NodePort'  # 网关类型
        annotations = {"servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        # 创建网关
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            project_steps.step_create_gateway_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0],
                                                               type=type, annotations=annotations)
            # 查询网关
            response = project_steps.step_get_gateway_in_multi_project(cluster_name=project_info[1],
                                                                       project_name=project_info[0])
            # 获取网关的类型
            gateway_type = response.json()['spec']['type']
            # 验证网关创建正确
            assert gateway_type == type
            # 验证网关创建成功
            assert response.status_code == 200
            # 删除网关
            project_steps.step_delete_gateway_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0])
            # 验证网关删除成功
            response = project_steps.step_get_gateway_in_multi_project(cluster_name=project_info[1],
                                                                       project_name=project_info[0])
            assert response.json()['message'] == 'service \"kubesphere-router-' + project_info[0] + '\" not found'

    @allure.story('项目设置-高级设置')
    @allure.title('在多集群项目设置网关-LoadBalancer')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_gateway_loadbalancer(self):
        type = 'LoadBalancer'  # 网关类型
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0",
                       "servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        # 创建网关
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            project_steps.step_create_gateway_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0],
                                                               type=type, annotations=annotations)
            # 查询网关
            response = project_steps.step_get_gateway_in_multi_project(cluster_name=project_info[1],
                                                                       project_name=project_info[0])
            # 获取网关的类型
            gateway_type = response.json()['spec']['type']
            # 验证网关创建正确
            assert gateway_type == type
            # 验证网关创建成功
            assert response.status_code == 200
            # # 删除网关
            project_steps.step_delete_gateway_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0])
            # 验证网关删除成功
            response = project_steps.step_get_gateway_in_multi_project(cluster_name=project_info[1],
                                                                       project_name=project_info[0])
            assert response.json()['message'] == 'service \"kubesphere-router-' + project_info[0] + '\" not found'

    @allure.story('项目设置-高级设置')
    @allure.title('在多集群项目编辑网关')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_gateway(self):
        type = 'LoadBalancer'  # 网关类型
        type_new = 'NodePort'
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0",
                       "servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        annotations_new = {"servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 创建网关
            project_steps.step_create_gateway_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0],
                                                               type=type, annotations=annotations)
            # 编辑网关
            project_steps.step_edit_gateway_in_multi_project(cluster_name=project_info[1],
                                                             project_name=project_info[0],
                                                             type=type_new, annotations=annotations_new)
            # 查询网关
            response = project_steps.step_get_gateway_in_multi_project(cluster_name=project_info[1],
                                                                       project_name=project_info[0])
            # 获取网关的注释信息
            gateway_annotations = response.json()['metadata']['annotations']
            # 验证网关修改成功
            assert gateway_annotations == annotations_new
            # 删除网关
            project_steps.step_delete_gateway_in_multi_project(cluster_name=project_info[1],
                                                               project_name=project_info[0])

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目修改工作负载副本并验证运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_work_replica(self):
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            condition = 'name=' + workload_name  # 查询条件
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建工作负载
            project_steps.step_create_deploy_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0], work_name=workload_name,
                                                              container_name=container_name, ports=port,
                                                              volumemount=volumeMounts,
                                                              image=image, replicas=replicas, volume_info=volume_info,
                                                              strategy=strategy_info)

            # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
            i = 0
            while i < 60:
                response = project_steps.step_get_workload_in_multi_project(cluster_name=project_info[1],
                                                                            project_name=project_info[0],
                                                                            type='deployments', condition=condition)
                try:
                    status = response.json()['items'][0]['status']
                except Exception as e:
                    print(e)
                    # 删除deployment
                    project_steps.step_delete_workload_in_multi_project(project_name=project_info[0],
                                                                        type='deployments', work_name=workload_name)
                    pytest.xfail('deploymenet创建失败，标记为xfail')
                    break
                # 验证资源的所有副本已就绪
                if 'unavailableReplicas' not in status:
                    print('创建工作负载耗时:' + str(i) + 's')
                    break
                time.sleep(1)
                i = i + 1
            assert 'unavailableReplicas' not in status

            replicas_new = 3  # 副本数
            # 修改副本数
            project_steps.step_modify_work_replicas_in_multi_project(cluster_name=project_info[1],
                                                                     project_name=project_info[0], type='deployments',
                                                                     work_name=workload_name, replicas=replicas_new)
            # 获取工作负载中所有的容器组，并验证其运行正常，最长等待时间60s
            time.sleep(5)
            # 查询容器的信息
            re = project_steps.step_get_work_pod_info_in_multi_project(cluster_name=project_info[1],
                                                                       project_name=project_info[0],
                                                                       work_name=workload_name)
            pod_count = re.json()['totalItems']
            # 验证pod数量正确
            assert pod_count == replicas_new
            # 获取并验证所有的pod运行正常
            for j in range(pod_count):
                i = 0
                while i < 60:
                    r = project_steps.step_get_work_pod_info_in_multi_project(cluster_name=project_info[1],
                                                                              project_name=project_info[0],
                                                                              work_name=workload_name)
                    status = r.json()['items'][j]['status']['phase']
                    if status == 'Running':
                        break
                    else:
                        time.sleep(5)
                        i = i + 5
                assert status == 'Running'

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目删除存在的存储卷，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_volume(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            volume_name = 'volume-stateful' + str(commonFunction.get_random())  # 存储卷的名称
            # 创建存储卷
            project_steps.step_create_volume_in_multi_project(cluster_name=project_info[1],
                                                              project_name=project_info[0], volume_name=volume_name)
            # 删除存储卷
            project_steps.step_delete_volume_in_multi_project(project_info[0], volume_name)
            # 查询被删除的存储卷
            i = 0
            # 验证存储卷被删除，最长等待时间为30s
            while i < 30:
                response = project_steps.step_get_volume(self.project_name, self.volume_name)
                # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
                if response.json()['totalItems'] == 0:
                    print("删除存储卷耗时:" + str(i) + '秒')
                    break
                time.sleep(1)
                i = i + 1
            print("actual_result:r1.json()['totalItems'] = " + str(response.json()['totalItems']))
            print("expect_result: 0")
            # 验证存储卷成功
            assert response.json()['totalItems'] == 0

    @allure.story('项目设置-基本信息')
    @allure.title('编辑多集群项目信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_project(self):
        alias_name = 'test-231313!#!G@#K!G#G!PG#'  # 别名信息
        description = '测试test123！@#'  # 描述信息
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 编辑项目信息
            response = project_steps.step_edit_project_in_multi_project(cluster_name=project_info[1],
                                                                        ws_name=project_info[2],
                                                                        project_name=project_info[0],
                                                                        alias_name=alias_name, description=description)
            # 验证编辑成功
            assert response.status_code == 200

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-CPU')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_project_quota_cpu(self):
        # 配额信息
        hard = {"limits.cpu": "40",
                "requests.cpu": "40"
                }
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                   resource_version)
            # 获取修改后的配额信息
            response = project_steps.step_get_project_quota_in_multi_project(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-输入错误的cpu信息(包含字母)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_cpu(self):
        # 配额信息,错误的cpu信息
        hard = {"limits.cpu": "11www",
                "requests.cpu": "1www"
                }
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            r = project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                       resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-输入错误的cpu信息(包含负数)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_cpu_1(self):
        # 配额信息,错误的cpu信息
        hard = {"limits.cpu": "-11",
                "requests.cpu": "1"
                }
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            r = project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                       resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-内存')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_memory(self):
        # 配额信息
        hard = {"limits.memory": "1000Gi", "requests.memory": "1Gi"}
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                   resource_version)
            # 获取修改后的配额信息
            response = project_steps.step_get_project_quota_in_multi_project(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-输入错误的内存(包含非单位字母)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_memory_1(self):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Giw"}
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            r = project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                       resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-输入错误的内存(包含负数)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_memory_2(self):
        # 配额信息
        hard = {"limits.memory": "-10Gi", "requests.memory": "1Gi"}
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            r = project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                       resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-CPU、内存')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_cpu_memory(self):
        # 配额信息
        hard = {"limits.memory": "1000Gi", "requests.memory": "1Gi",
                "limits.cpu": "100", "requests.cpu": "100"}
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                   resource_version)
            # 获取修改后的配额信息
            response = project_steps.step_get_project_quota_in_multi_project(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-资源配额')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_resource(self):
        # 配额信息
        hard = {"count/pods": "100",
                "count/deployments.apps": "6",
                "count/statefulsets.apps": "6",
                "count/jobs.batch": "1",
                "count/services": "5",
                "persistentvolumeclaims": "6",
                "count/daemonsets.apps": "5",
                "count/cronjobs.batch": "4",
                "count/ingresses.extensions": "4",
                "count/secrets": "8",
                "count/configmaps": "7"}
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                   resource_version)
            # 获取修改后的配额信息
            response = project_steps.step_get_project_quota_in_multi_project(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-输入错误的资源配额信息(包含字母)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_resource(self):
        # 配额信息
        hard = {"count/pods": "100q",
                "count/deployments.apps": "6",
                "count/statefulsets.apps": "6",
                "count/jobs.batch": "1",
                "count/services": "5",
                "persistentvolumeclaims": "6",
                "count/daemonsets.apps": "5",
                "count/cronjobs.batch": "4",
                "count/ingresses.extensions": "4",
                "count/secrets": "8",
                "count/configmaps": "7"}
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            r = project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                       resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-输入错误的资源配额信息(包含负数)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_resource_1(self):
        # 配额信息
        hard = {"count/pods": "-100",
                "count/deployments.apps": "6",
                "count/statefulsets.apps": "6",
                "count/jobs.batch": "1",
                "count/services": "5",
                "persistentvolumeclaims": "6",
                "count/daemonsets.apps": "5",
                "count/cronjobs.batch": "4",
                "count/ingresses.extensions": "4",
                "count/secrets": "8",
                "count/configmaps": "7"}
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            r = project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                       resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群下项目设置项目配额-cpu、memory、资源配额')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota(self):
        # 配额信息
        hard = {"count/configmaps": "7",
                "count/cronjobs.batch": "4",
                "count/daemonsets.apps": "5",
                "count/deployments.apps": "6",
                "count/ingresses.extensions": "4",
                "count/jobs.batch": "1",
                "count/pods": "100",
                "count/secrets": "8",
                "count/services": "5",
                "count/statefulsets.apps": "6",
                "persistentvolumeclaims": "6",
                "limits.cpu": "200", "limits.memory": "1000Gi",
                "requests.cpu": "200", "requests.memory": "3Gi"}
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = project_steps.step_get_project_quota_version_in_multi_project(project_info[1],
                                                                                             project_info[0])
            # 编辑配额信息
            project_steps.step_edit_project_quota_in_multi_project(project_info[1], project_info[0], hard,
                                                                   resource_version)
            # 获取修改后的配额信息
            response = project_steps.step_get_project_quota_in_multi_project(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-资源默认请求')
    @allure.title('在多集群项目只设置资源默认请求-cpu')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_cpu(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取资源默认请求
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"cpu": "16"}
            request = {"cpu": "2"}
            project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
                                                                     resource_version, limit, request)
            # 查询编辑结果
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            limit_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['default']
            request_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['defaultRequest']
            # 验证编辑成功
            assert limit == limit_actual
            assert request == request_actual

    @allure.story('项目设置-资源默认请求')
    @allure.title('在多集群项目只设置资源默认请求-输入错误的cpu信息(包含字母)')
    # 接口未做限制
    def wx_test_edit_container_quota_wrong_cpu(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取资源默认请求
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"cpu": "16aa"}
            request = {"cpu": "2"}
            r = project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
                                                                         resource_version, limit, request)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的cpu信息(包含负数)')
    # 接口未做限制
    def wx_test_edit_container_quota_wrong_cpu_1(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"cpu": "-16"}
            request = {"cpu": "-2"}
            r = project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
                                                                         resource_version, limit, request)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-内存')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_memory(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取资源默认请求
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"memory": "1000Mi"}
            request = {"memory": "1Mi"}
            project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0], resource_version,
                                                                     limit, request)
            # 查询编辑结果
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            limit_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['default']
            request_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['defaultRequest']
            # 验证编辑成功
            assert limit == limit_actual
            assert request == request_actual

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的内存信息(包含非单位字母)')
    # 接口未做限制
    def wx_test_edit_container_quota_wrong_memory(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"memory": "1000aMi"}
            request = {"memory": "1Mi"}
            r = project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
                                                                         resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的内存信息(包含负数)')
    # 接口未做限制
    def wx_test_edit_container_quota_wrong_memory_1(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"memory": "1000aMi"}
            request = {"memory": "1Mi"}
            r = project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
                                                                         resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('在多集群项目只设置资源默认请求-内存、cpu')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_memory_1(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取资源默认请求
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"cpu": "15", "memory": "1000Mi"}
            request = {"cpu": "2", "memory": "1Mi"}
            project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
                                                                     resource_version, limit, request)
            # 查询编辑结果
            response = project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
            limit_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['default']
            request_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['defaultRequest']
            # 验证编辑成功
            assert limit == limit_actual
            assert request == request_actual

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建默认类型的密钥')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_secret_default(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 在多集群项目创建默认类型的密钥
            secret_name = 'secret' + str(commonFunction.get_random())
            project_steps.step_create_secret_default_in_multi_project(cluster_name=project_info[1],
                                                                      project_name=project_info[0],
                                                                      secret_name=secret_name, key='wx',
                                                                      value='dGVzdA==')
            i = 0
            while i < 100:
                try:
                    # 查询创建的密钥
                    response = project_steps.step_get_federatedsecret(project_name=project_info[0], secret_name=secret_name)
                    # 获取密钥的数量和状态
                    secret_count = response.json()['totalItems']
                    secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
                    if secret_status:
                        break
                    else:
                        time.sleep(3)
                        i += 3
                except Exception as e:
                    print(e)
            # 验证查询到的密钥数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的密钥
            project_steps.step_delete_federatedsecret(project_name=project_info[0], secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建TLS类型的密钥')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_secret_tls(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 在多集群项目创建默认类型的密钥
            secret_name = 'secret' + str(commonFunction.get_random())
            project_steps.step_create_secret_tls_in_multi_project(cluster_name=project_info[1],
                                                                  project_name=project_info[0],
                                                                  secret_name=secret_name, credential='d3g=',
                                                                  key='dGVzdA==')
            i = 0
            while i < 100:
                try:
                    # 查询创建的密钥
                    response = project_steps.step_get_federatedsecret(project_name=project_info[0], secret_name=secret_name)
                    # 获取密钥的数量和状态
                    secret_count = response.json()['totalItems']
                    secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
                    if secret_status:
                        break
                    else:
                        time.sleep(3)
                        i += 3
                except Exception as e:
                    print(e)
            # 验证查询到的密钥数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的密钥
            project_steps.step_delete_federatedsecret(project_name=project_info[0], secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建image类型的密钥')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_secret_image(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 在多集群项目创建默认类型的密钥
            secret_name = 'secret' + str(commonFunction.get_random())
            project_steps.step_create_secret_image_in_multi_project(cluster_name=project_info[1],
                                                                    project_name=project_info[0],
                                                                    secret_name=secret_name)
            i = 0
            while i < 100:
                # 查询创建的密钥
                try:
                    response = project_steps.step_get_federatedsecret(project_name=project_info[0], secret_name=secret_name)
                    # 获取密钥的数量和状态
                    secret_count = response.json()['totalItems']
                    secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
                    if secret_status:
                        break
                    else:
                        time.sleep(3)
                        i += 3
                except Exception as e:
                    print(e)
            # 验证查询到的密钥数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的密钥
            project_steps.step_delete_federatedsecret(project_name=project_info[0], secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建账号密码类型的密钥')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_secret_account(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 在多集群项目创建默认类型的密钥
            secret_name = 'secret' + str(commonFunction.get_random())
            project_steps.step_create_secret_account_in_multi_project(cluster_name=project_info[1],
                                                                      project_name=project_info[0],
                                                                      secret_name=secret_name, username='d3g=',
                                                                      password='dGVzdA==')
            i = 0
            while i < 100:
                try:
                    # 查询创建的密钥
                    response = project_steps.step_get_federatedsecret(project_name=project_info[0], secret_name=secret_name)
                    # 获取密钥的数量和状态
                    secret_count = response.json()['totalItems']
                    secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
                    if secret_status:
                        break
                    else:
                        time.sleep(3)
                        i += 3
                except Exception as e:
                    print(e)
            # 验证查询到的密钥数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的密钥
            project_steps.step_delete_federatedsecret(project_name=project_info[0], secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建配置')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_config_map(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            config_name = 'config-map' + str(commonFunction.get_random())
            # 在每个多集群项目创建配置
            project_steps.step_create_config_map_in_multi_project(cluster_name=project_info[1],
                                                                  project_name=project_info[0],
                                                                  config_name=config_name, key='wx', value='test')
            i = 0
            while i < 100:
                try:
                    # 查询创建的配置
                    response = project_steps.step_get_federatedconfigmap(project_name=project_info[0], config_name=config_name)
                    # 获取配置的数量和状态
                    secret_count = response.json()['totalItems']
                    secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
                    if secret_status:
                        break
                    else:
                        time.sleep(3)
                        i += 3
                except Exception as e:
                    print(e)
            # 验证查询到的配置数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的配置
            project_steps.step_delete_config_map(project_name=project_info[0], config_name=config_name)

    @allure.story('项目设置-高级设置')
    @allure.title('落盘日志收集-开启')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('logging') is False, reason='集群未开启logging功能')
    def test_disk_log_collection_open(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 开启落盘日志收集功能
            project_steps.step_set_disk_log_collection(project_name=project_info[0], set='enabled')
            # 查看落盘日志收集功能
            response = project_steps.step_check_disk_log_collection(project_name=project_info[0])
            # 获取功能状态
            status = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
            # 验证功能开启成功
            assert status == 'enabled'

    @allure.story('项目设置-高级设置')
    @allure.title('落盘日志收集-关闭')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('logging') is False, reason='集群未开启logging功能')
    def test_disk_log_collection_close(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 关闭落盘日志收集功能
            project_steps.step_set_disk_log_collection(project_name=project_info[0], set='disabled')
            # 查看落盘日志收集功能
            response = project_steps.step_check_disk_log_collection(project_name=project_info[0])
            # 获取功能状态
            status = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
            # 验证功能开启成功
            assert status == 'disabled'

    @allure.story('概览')
    @allure.title('查询多集群项目的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_project_metrics(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取720分钟之前的戳
            before_timestamp = commonFunction.get_before_timestamp(720)
            # 查询每个项目最近12h的监控信息
            response = project_steps.step_get_project_metrics_in_multi_project(cluster_name=project_info[1],
                                                                               project_name=project_info[0],
                                                                               start_time=before_timestamp,
                                                                               end_time=now_timestamp,
                                                                               step='4320s', times=str(10))
            # 获取结果中的数据类型
            type = response.json()['results'][0]['data']['resultType']
            # 验证数据类型正确
            assert type == 'matrix'

    @allure.story('概览')
    @allure.title('查询多集群项目的abnormalworkloads')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_project_abnormalworkloads(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 查询多集群项目的abnormalworkloads
            response = project_steps.step_get_project_abnormalworkloads_in_multi_project(cluster_name=project_info[1],
                                                                                         project_name=project_info[0])
            # 验证查询成功
            assert 'persistentvolumeclaims' in response.json()['data']

    @allure.story('概览')
    @allure.title('查询多集群项目的federatedlimitranges')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_project_federatedlimitranges(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            # 查询多集群项目的federatedlimitranges
            response = project_steps.step_get_project_federatedlimitranges(project_name=project_info[0])
            # 获取查询结果中的kind
            kind = response.json()['kind']
            # 验证kind正确
            assert kind == 'FederatedLimitRangeList'

    @allure.story('概览')
    @allure.title('查询多集群项目的workloads')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_project_workloads(self):
        # 获取环境中所有的多集群项目
        multi_projects = project_steps.step_get_multi_project_all(self.ws_name)
        for project_info in multi_projects:
            response = project_steps.step_get_project_workloads_in_multi_project(cluster_name=project_info[1],
                                                                                 project_name=project_info[0])
            # 验证查询成功
            assert response.json()['total_item'] >= 0


if __name__ == "__main__":
    pytest.main(['-s', 'testProject.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
