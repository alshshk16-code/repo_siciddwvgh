#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ᚺᚾᛉᚲᛏ Shodan's Spear - وحدة الصيد والاستهداف
محرك البحث والاستهداف الذكي باستخدام Shodan API
"""

import shodan
import time
import random
from typing import List, Dict, Optional
from config import *

class Hunter:
    """
    وحدة الصيد - محرك البحث عن الأهداف الضعيفة
    """
    
    def __init__(self, api_key: str):
        """
        تهيئة محرك الصيد
        
        Args:
            api_key: مفتاح Shodan API
        """
        if not api_key:
            raise ValueError(MESSAGES["no_api_key"])
        
        self.api = shodan.Shodan(api_key)
        self.targets = []
        self.stats = {
            "total_found": 0,
            "queries_executed": 0,
            "errors": 0
        }
    
    def get_api_info(self) -> Dict:
        """
        الحصول على معلومات حساب Shodan API
        
        Returns:
            معلومات الحساب
        """
        try:
            info = self.api.info()
            return {
                "plan": info.get("plan", "غير معروف"),
                "query_credits": info.get("query_credits", 0),
                "scan_credits": info.get("scan_credits", 0),
                "usage_limits": info.get("usage_limits", {})
            }
        except Exception as e:
            return {"error": str(e)}
    
    def hunt(self, query_name: str, max_results: int = None) -> List[Dict]:
        """
        البحث عن أهداف باستخدام استعلام محدد
        
        Args:
            query_name: اسم الاستعلام من HUNT_QUERIES
            max_results: الحد الأقصى للنتائج (افتراضي من config)
        
        Returns:
            قائمة الأهداف المكتشفة
        """
        if query_name not in HUNT_QUERIES:
            raise ValueError(f"استعلام غير معروف: {query_name}")
        
        query_config = HUNT_QUERIES[query_name]
        query = query_config["query"]
        max_results = max_results or RESULTS_PER_QUERY
        
        targets = []
        
        try:
            print(f"{Colors.CYAN}{Icons.WORLD} جاري البحث: {query_config['description']}{Colors.RESET}")
            print(f"{Colors.DIM}   الاستعلام: {query}{Colors.RESET}")
            
            # تنفيذ البحث
            results = self.api.search(query, limit=max_results)
            
            self.stats["queries_executed"] += 1
            self.stats["total_found"] += results['total']
            
            print(f"{Colors.GREEN}{Icons.SUCCESS} تم العثور على {results['total']} هدف محتمل{Colors.RESET}")
            
            # معالجة النتائج
            for result in results['matches']:
                target = {
                    "ip": result.get("ip_str"),
                    "port": result.get("port"),
                    "hostname": result.get("hostnames", [""])[0] if result.get("hostnames") else "",
                    "organization": result.get("org", "غير معروف"),
                    "country": result.get("location", {}).get("country_name", "غير معروف"),
                    "city": result.get("location", {}).get("city", "غير معروف"),
                    "banner": result.get("data", "")[:200],  # أول 200 حرف
                    "timestamp": result.get("timestamp"),
                    "query_type": query_name,
                    "attack_type": query_config["attack_type"],
                    "description": query_config["description"],
                    "status": "pending",  # pending, success, failed
                    "loot": None
                }
                targets.append(target)
            
            self.targets.extend(targets)
            
            # تأخير صغير لتجنب تجاوز حدود API
            time.sleep(1)
            
            return targets
            
        except shodan.APIError as e:
            self.stats["errors"] += 1
            print(f"{Colors.RED}{Icons.FAILED} خطأ في API: {str(e)}{Colors.RESET}")
            return []
        except Exception as e:
            self.stats["errors"] += 1
            print(f"{Colors.RED}{Icons.FAILED} خطأ غير متوقع: {str(e)}{Colors.RESET}")
            return []
    
    def hunt_all(self, max_results_per_query: int = None) -> List[Dict]:
        """
        البحث باستخدام جميع الاستعلامات المتاحة
        
        Args:
            max_results_per_query: الحد الأقصى للنتائج لكل استعلام
        
        Returns:
            قائمة جميع الأهداف المكتشفة
        """
        all_targets = []
        
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{Icons.FIRE} بدء عملية الصيد الشاملة{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═' * 60}{Colors.RESET}\n")
        
        for query_name in HUNT_QUERIES.keys():
            targets = self.hunt(query_name, max_results_per_query)
            all_targets.extend(targets)
            
            # تأخير بين الاستعلامات
            time.sleep(random.uniform(1, 3))
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}{Icons.SUCCESS} اكتمل الصيد!{Colors.RESET}")
        print(f"{Colors.GREEN}   إجمالي الأهداف: {len(all_targets)}{Colors.RESET}\n")
        
        return all_targets
    
    def hunt_specific(self, custom_query: str, max_results: int = None) -> List[Dict]:
        """
        البحث باستخدام استعلام مخصص
        
        Args:
            custom_query: استعلام Shodan مخصص
            max_results: الحد الأقصى للنتائج
        
        Returns:
            قائمة الأهداف المكتشفة
        """
        max_results = max_results or RESULTS_PER_QUERY
        targets = []
        
        try:
            print(f"{Colors.CYAN}{Icons.WORLD} جاري البحث المخصص...{Colors.RESET}")
            print(f"{Colors.DIM}   الاستعلام: {custom_query}{Colors.RESET}")
            
            results = self.api.search(custom_query, limit=max_results)
            
            self.stats["queries_executed"] += 1
            self.stats["total_found"] += results['total']
            
            print(f"{Colors.GREEN}{Icons.SUCCESS} تم العثور على {results['total']} هدف{Colors.RESET}")
            
            for result in results['matches']:
                target = {
                    "ip": result.get("ip_str"),
                    "port": result.get("port"),
                    "hostname": result.get("hostnames", [""])[0] if result.get("hostnames") else "",
                    "organization": result.get("org", "غير معروف"),
                    "country": result.get("location", {}).get("country_name", "غير معروف"),
                    "city": result.get("location", {}).get("city", "غير معروف"),
                    "banner": result.get("data", "")[:200],
                    "timestamp": result.get("timestamp"),
                    "query_type": "custom",
                    "attack_type": "custom",
                    "description": "استعلام مخصص",
                    "status": "pending",
                    "loot": None
                }
                targets.append(target)
            
            self.targets.extend(targets)
            time.sleep(1)
            
            return targets
            
        except Exception as e:
            self.stats["errors"] += 1
            print(f"{Colors.RED}{Icons.FAILED} خطأ: {str(e)}{Colors.RESET}")
            return []
    
    def get_stats(self) -> Dict:
        """
        الحصول على إحصائيات الصيد
        
        Returns:
            إحصائيات الصيد
        """
        return {
            **self.stats,
            "targets_count": len(self.targets),
            "pending": len([t for t in self.targets if t["status"] == "pending"]),
            "success": len([t for t in self.targets if t["status"] == "success"]),
            "failed": len([t for t in self.targets if t["status"] == "failed"])
        }
    
    def clear_targets(self):
        """مسح قائمة الأهداف"""
        self.targets = []
    
    def get_targets_by_type(self, attack_type: str) -> List[Dict]:
        """
        الحصول على الأهداف حسب نوع الهجوم
        
        Args:
            attack_type: نوع الهجوم
        
        Returns:
            قائمة الأهداف المطابقة
        """
        return [t for t in self.targets if t["attack_type"] == attack_type]
    
    def get_targets_by_country(self, country: str) -> List[Dict]:
        """
        الحصول على الأهداف حسب الدولة
        
        Args:
            country: اسم الدولة
        
        Returns:
            قائمة الأهداف المطابقة
        """
        return [t for t in self.targets if country.lower() in t["country"].lower()]
