import requests
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getHeader import get_header
from common import commonFunction


@allure.step('修改角色权限')
def step_edit_role_authory(ws_name, role_name, version, authory):
    # 修改角色的url地址
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles/' + role_name
    # 修改目标角色的数据
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "WorkspaceRole",
            "metadata": {"name": role_name,
                         "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"iam.kubesphere.io/aggregation-roles": authory,
                                         "kubesphere.io/creator": "admin"},
                         "resourceVersion": version
                         }
            }
    response = requests.put(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建企业空间的角色')
def step_create_ws_role(ws_name, ws_role_name, authory):
    """
    :param ws_name: 企业空间的名称
    :param ws_role_name: 企业空间的角色的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "WorkspaceRole",
            "rules": [],
            "metadata": {"name": ws_role_name,
                         "annotations": {"iam.kubesphere.io/aggregation-roles": authory,
                                         "kubesphere.io/creator": "admin"}
                         }
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询企业空间指定角色')
def step_get_ws_role(ws_name, role_name):
    """
    :param role_name:
    :param ws_name: 企业空间的名称
    :return: 企业空间中第一个角色的resourceversion
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles?name=' + role_name \
          + '&sortBy=createTime&limit=10&annotation=kubesphere.io%2Fcreator'

    response = requests.get(url, headers=get_header())
    return response


@allure.step('查询企业空间指定成员')
def step_get_ws_user(ws_name, user_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspacemembers?name=' + user_name
    response = requests.get(url, headers=get_header())
    return response


@allure.step('删除企业空间角色')
def step_delete_role(ws_name, role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles/' + role_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('邀请用户到企业空间')
def step_invite_user(ws_name, user_name, role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspacemembers'
    # 邀请成员的信息
    data = [{"username": user_name, "roleRef": role_name}]
    # 邀请成员
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('修改企业成员的角色')
def step_edit_ws_user_role(ws_name, user_name, role_name):
    # 修改企业空间成员角色的url地址
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspacemembers/' + user_name
    # 修改的目标数据
    data = {"username": user_name,
            "roleRef": role_name}
    # 修改成员角色
    response = requests.put(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('将用户从企业空间移除')
def step_delete_ws_user(ws_name, user_name):
    # 删除邀请成员的url地址
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspacemembers/' + user_name
    # 删除邀请成员
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('在企业空间中查询指定用户')
def step_get_ws_user(ws_name, user_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspacemembers?name=' + user_name
    response = requests.get(url, headers=get_header())
    return response


@allure.step('创建企业组织')
def step_create_department(ws_name, group_name, data):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/groups'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "Group",
            "metadata": {
                "annotations": data,
                "labels": {"kubesphere.io/workspace": "wsp1", "iam.kubesphere.io/group-parent": "root"},
                "generateName": group_name}
            }

    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    return r


@allure.step('查看企业组织可分配的用户信息')
def step_get_user_for_department(name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users?notingroup=' + name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看企业组织已分配的用户信息')
def step_get_user_assigned_department(name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users?ingroup=' + name
    response = requests.get(url)
    return response


@allure.step('将指定用户绑定到指定企业组织')
def step_binding_user(ws_name, group_name, user_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/groupbindings'
    data = [{"userName": user_name, "groupName": group_name}]
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('将用户从企业组织解绑')
def step_unbind_user(ws_name, user_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/groupbindings/' + user_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询企业组织')
def step_get_department(ws_name):
    """
    :param ws_name: 企业空间名称
    :return: 所有的企业组织名称
    """
    name_list = []
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/groups'
    r = requests.get(url=url, headers=get_header())
    count = r.json()['totalItems']
    for i in range(0, count):
        name_list.append(r.json()['items'][i]['metadata']['generateName'])

    return name_list


@allure.step('编辑企业组织')
def step_edit_department(ws_name, group_name, data):
    """
    :param data: 需要编辑的数据
    :param ws_name: 企业空间名称
    :param group_name: 企业组织的名称
    :return:
    """
    # 修改企业空间的annotations信息，并返回annotations
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/groups/' + group_name
    r = requests.patch(url=url, headers=get_header(), data=json.dumps(data))
    return r.json()['metadata']['annotations']


@allure.step('删除企业组织')
def step_delete_department(ws_name, group_name):
    """

    :param ws_name: 企业空间名称
    :param group_name: 企业组织name
    :return:
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/groups/' + group_name
    r = requests.delete(url=url, headers=get_header())
    return r


@allure.step('初始化企业配额')
def step_init_quota(ws_name, cluster):
    data = {"apiVersion": "quota.kubesphere.io/v1alpha2", "kind": "ResourceQuota",
            "metadata": {"name": ws_name, "workspace": ws_name, "cluster": cluster,
                         "annotations": {"kubesphere.io/creator": "admin"}}, "spec": {"quota": {"hard": {}}}}
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/resourcequotas'
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('获取企业配额的信息')
def step_get_quota_resource_version(ws_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/resourcequotas/' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('编辑企业配额')
def step_edit_quota(ws_name, hard_data, cluster, resource_version):
    data = {"apiVersion": "quota.kubesphere.io/v1alpha2", "kind": "ResourceQuota",
            "metadata": {"name": ws_name, "workspace": ws_name, "cluster": cluster,
                         "resourceVersion": resource_version},
            "spec": {"quota": {"hard": hard_data}}}

    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/resourcequotas/' + ws_name
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建用户')
def step_create_user(user_name):
    """
    :param user_name: 系统用户的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users'
    email = 'stevewen' + str(commonFunction.get_random()) + '@yunify.com'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "User",
            "metadata": {"name": user_name,
                         "annotations": {"kubesphere.io/creator": "admin"}
                         },
            "spec": {"email": email,
                     "password": "P@88w0rd"}
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建企业空间')
def step_create_workspace(ws_name):
    """
    :param ws_name: 企业空间的名称
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
    data = {"apiVersion": "tenant.kubesphere.io/v1alpha2",
            "kind": "WorkspaceTemplate",
            "metadata": {"name": ws_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"template": {"spec": {"manager": "admin"}}}}
    requests.post(url, headers=get_header(), data=json.dumps(data))


@allure.step('创建多集群企业空间')
def step_create_multi_ws(ws_name, alias_name, description, cluster_names):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
    clusters = []
    if isinstance(cluster_names, str):
        clusters.append({'name': cluster_names})
    else:
        for cluster_name in cluster_names:
            clusters.append({'name': cluster_name})
    data = {"apiVersion": "tenant.kubesphere.io/v1alpha2",
            "kind": "WorkspaceTemplate",
            "metadata":
                {"name": ws_name,
                 "annotations": {
                     "kubesphere.io/alias-name": alias_name,
                     "kubesphere.io/description": description,
                     "kubesphere.io/creator": "admin"}
                 },
            "spec": {"template": {"spec": {"manager": "admin"}},
                     "placement": {"clusters": clusters}}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('删除企业空间')
def step_delete_workspace(ws_name):
    """
    :param ws_name: 企业空间的名称
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('删除用户')
def step_delete_user(user_name):
    """
    :param user_name: 系统用户的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users/' + user_name
    requests.delete(url, headers=get_header())


@allure.step('开关企业空间网络隔离')
def step_set_network_lsolation(ws_name, status):
    """

    :param ws_name:
    :param status: True or False
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name
    data = {"spec": {"template": {"spec": {"networkIsolation": status}}}}
    response = requests.patch(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在单集群环境查询企业空间')
def step_get_ws_info(ws_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces?name=' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询企业空间的项目信息')
def step_get_project_info(ws_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces?' \
          'sortBy=createTime&labelSelector=%21kubesphere.io%2Fkubefed-host-namespace%2C%21kubesphere.io%2Fdevopsproject'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建多集群企业空间')
def step_create_multi_ws(ws_name, alias_name, description, cluster_names):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
    clusters = []
    if isinstance(cluster_names, str):
        clusters.append({'name': cluster_names})
    else:
        for cluster_name in cluster_names:
            clusters.append({'name': cluster_name})
    data = {"apiVersion": "tenant.kubesphere.io/v1alpha2",
            "kind": "WorkspaceTemplate",
            "metadata":
                {"name": ws_name,
                 "annotations": {
                     "kubesphere.io/alias-name": alias_name,
                     "kubesphere.io/description": description,
                     "kubesphere.io/creator": "admin"}
                 },
            "spec": {"template": {"spec": {"manager": "admin"}},
                     "placement": {"clusters": clusters}}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response



