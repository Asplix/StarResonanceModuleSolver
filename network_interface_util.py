"""
网络接口工具
用于获取和选择网络接口
"""

import subprocess
import socket
import psutil
from typing import List, Dict, Optional, Tuple


def get_network_interfaces() -> List[Dict]:
    """
    获取所有网络接口信息
    
    Returns:
        网络接口列表, 每个接口包含name、description、addresses等信息
    """
    interfaces = []
    
    try:
        # 使用psutil获取网络接口信息
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for interface_name, addresses in net_if_addrs.items():
            # 获取接口状态
            stats = net_if_stats.get(interface_name)
            
            # 过滤掉回环接口和虚拟接口
            if interface_name.startswith(('lo', 'Loopback', 'vEthernet', 'VMware')):
                continue
                
            # 获取IPv4地址
            ipv4_addresses = []
            for addr in addresses:
                if addr.family == socket.AF_INET:
                    ipv4_addresses.append({
                        'addr': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': getattr(addr, 'broadcast', None)
                    })
            
            # 只包含有IPv4地址的接口
            if ipv4_addresses:
                interface_info = {
                    'name': interface_name,
                    'description': interface_name,
                    'addresses': ipv4_addresses,
                    'is_up': stats.isup if stats else False,
                    'speed': stats.speed if stats else 0
                }
                interfaces.append(interface_info)
                
    except Exception as e:
        print(f"Failed to get network interfaces: {e}")
        
    return interfaces


def find_default_network_interface(interfaces: List[Dict]) -> Optional[int]:
    """
    查找默认网络接口
    
    Args:
        interfaces: 网络接口列表
        
    Returns:
        默认接口的索引, 如果未找到则返回None
    """
    try:
        if hasattr(subprocess, 'run'):
            result = subprocess.run(
                ['route', 'print', '0.0.0.0'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('0.0.0.0'):
                        parts = line.split()
                        if len(parts) >= 4:
                            default_gateway = parts[3]
                            
                            # 查找包含默认网关的接口
                            for i, interface in enumerate(interfaces):
                                for addr_info in interface['addresses']:
                                    if addr_info['addr'] == default_gateway:
                                        return i
                                        
    except Exception as e:
        # 查找失败时不输出错误，静默处理
        pass
        
    # 如果无法找到默认接口，尝试使用第一个活动的接口
    for i, interface in enumerate(interfaces):
        if interface.get('is_up', False):
            return i
            
    return None


def display_network_interfaces(interfaces: List[Dict]) -> None:
    """
    显示网络接口列表
    
    Args:
        interfaces: 网络接口列表
    """
    print("Available network interfaces:")
    for i, interface in enumerate(interfaces):
        name = interface['name']
        description = interface.get('description', name)
        is_up = "✓" if interface.get('is_up', False) else "✗"
        addresses = [addr['addr'] for addr in interface['addresses']]
        addr_str = ", ".join(addresses) if addresses else "No IP Address"
        
        print(f"  {i:2d}. {is_up} {description}")
        print(f"      Address: {addr_str}")
        print(f"      Name: {name}")
        print()


def select_network_interface(interfaces: List[Dict], auto_detect: bool = False) -> Optional[int]:
    """
    选择网络接口
    
    Args:
        interfaces: 网络接口列表
        auto_detect: 是否自动检测默认接口
        
    Returns:
        选择的接口索引
    """
    if not interfaces:
        print("No available network interfaces found!")
        return None
        
    if auto_detect:
        print("Auto-detecting default network interface...")
        default_index = find_default_network_interface(interfaces)
        if default_index is not None:
            interface = interfaces[default_index]
            print(f"Using network interface: {default_index} - {interface['description']}")
            return default_index
        else:
            print("Default network interface not found!")
            
    # 显示接口列表
    display_network_interfaces(interfaces)
    
    # 交互式选择
    while True:
        try:
            choice = input("Please enter the number of the network interface to use: ").strip()
            if not choice:
                # 如果用户直接回车，尝试自动检测
                print("Auto-detecting default network interface...")
                default_index = find_default_network_interface(interfaces)
                if default_index is not None:
                    interface = interfaces[default_index]
                    print(f"Using network interface: {default_index} - {interface['description']}")
                    return default_index
                else:
                    print("Default network interface not found!")
                    continue
                    
            index = int(choice)
            if 0 <= index < len(interfaces):
                return index
            else:
                print(f"Invalid interface number: {index}")
        except ValueError:
            print("Please enter a valid number!")
        except KeyboardInterrupt:
            print("\nUser canceled selection")
            return None