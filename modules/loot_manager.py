#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ᚺᚾᛉᚲᛏ Shodan's Spear - نظام إدارة الغنائم
قاعدة بيانات وإدارة الأهداف المخترقة والغنائم
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from config import *

class LootManager:
    """
    مدير الغنائم - نظام إدارة وتخزين الأهداف المخترقة
    """
    
    def __init__(self, db_path: str = None):
        """
        تهيئة مدير الغنائم
        
        Args:
            db_path: مسار قاعدة البيانات
        """
        if db_path is None:
            db_path = str(DATA_DIR / "loot.db")
        
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """تهيئة قاعدة البيانات"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # جدول الأهداف
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                port INTEGER,
                hostname TEXT,
                organization TEXT,
                country TEXT,
                city TEXT,
                banner TEXT,
                query_type TEXT,
                attack_type TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attacked_at TIMESTAMP,
                UNIQUE(ip, port)
            )
        """)
        
        # جدول الغنائم
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                loot_type TEXT,
                method TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (target_id) REFERENCES targets(id)
            )
        """)
        
        # جدول الإحصائيات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT,
                stat_value INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def add_target(self, target: Dict) -> int:
        """
        إضافة هدف جديد
        
        Args:
            target: معلومات الهدف
        
        Returns:
            معرف الهدف
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO targets (
                    ip, port, hostname, organization, country, city,
                    banner, query_type, attack_type, description, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                target.get("ip"),
                target.get("port"),
                target.get("hostname", ""),
                target.get("organization", ""),
                target.get("country", ""),
                target.get("city", ""),
                target.get("banner", ""),
                target.get("query_type", ""),
                target.get("attack_type", ""),
                target.get("description", ""),
                target.get("status", "pending")
            ))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            # الهدف موجود بالفعل - تحديثه
            cursor.execute("""
                UPDATE targets SET
                    hostname = ?,
                    organization = ?,
                    country = ?,
                    city = ?,
                    banner = ?,
                    query_type = ?,
                    attack_type = ?,
                    description = ?
                WHERE ip = ? AND port = ?
            """, (
                target.get("hostname", ""),
                target.get("organization", ""),
                target.get("country", ""),
                target.get("city", ""),
                target.get("banner", ""),
                target.get("query_type", ""),
                target.get("attack_type", ""),
                target.get("description", ""),
                target.get("ip"),
                target.get("port")
            ))
            
            self.conn.commit()
            
            # الحصول على المعرف
            cursor.execute("SELECT id FROM targets WHERE ip = ? AND port = ?", 
                         (target.get("ip"), target.get("port")))
            return cursor.fetchone()[0]
    
    def add_targets_bulk(self, targets: List[Dict]) -> int:
        """
        إضافة أهداف متعددة دفعة واحدة
        
        Args:
            targets: قائمة الأهداف
        
        Returns:
            عدد الأهداف المضافة
        """
        added = 0
        for target in targets:
            try:
                self.add_target(target)
                added += 1
            except Exception as e:
                print(f"{Colors.RED}خطأ في إضافة الهدف {target.get('ip')}: {str(e)}{Colors.RESET}")
        
        return added
    
    def add_loot(self, target_id: int, loot_data: Dict):
        """
        إضافة غنيمة لهدف
        
        Args:
            target_id: معرف الهدف
            loot_data: بيانات الغنيمة
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO loot (target_id, loot_type, method, data)
            VALUES (?, ?, ?, ?)
        """, (
            target_id,
            loot_data.get("type", "unknown"),
            loot_data.get("method", "unknown"),
            json.dumps(loot_data, ensure_ascii=False)
        ))
        
        # تحديث حالة الهدف
        cursor.execute("""
            UPDATE targets 
            SET status = 'success', attacked_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (target_id,))
        
        self.conn.commit()
    
    def update_target_status(self, target_id: int, status: str):
        """
        تحديث حالة هدف
        
        Args:
            target_id: معرف الهدف
            status: الحالة الجديدة
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE targets 
            SET status = ?, attacked_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, target_id))
        self.conn.commit()
    
    def get_all_targets(self, status: str = None) -> List[Dict]:
        """
        الحصول على جميع الأهداف
        
        Args:
            status: تصفية حسب الحالة (اختياري)
        
        Returns:
            قائمة الأهداف
        """
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM targets WHERE status = ? ORDER BY discovered_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM targets ORDER BY discovered_at DESC")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_target_by_id(self, target_id: int) -> Optional[Dict]:
        """
        الحصول على هدف بواسطة المعرف
        
        Args:
            target_id: معرف الهدف
        
        Returns:
            معلومات الهدف
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM targets WHERE id = ?", (target_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_loot_by_target(self, target_id: int) -> List[Dict]:
        """
        الحصول على غنائم هدف معين
        
        Args:
            target_id: معرف الهدف
        
        Returns:
            قائمة الغنائم
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM loot WHERE target_id = ?", (target_id,))
        
        loot_list = []
        for row in cursor.fetchall():
            loot_dict = dict(row)
            loot_dict['data'] = json.loads(loot_dict['data'])
            loot_list.append(loot_dict)
        
        return loot_list
    
    def get_all_loot(self, loot_type: str = None) -> List[Dict]:
        """
        الحصول على جميع الغنائم
        
        Args:
            loot_type: تصفية حسب النوع (اختياري)
        
        Returns:
            قائمة الغنائم
        """
        cursor = self.conn.cursor()
        
        if loot_type:
            cursor.execute("""
                SELECT l.*, t.ip, t.port, t.country 
                FROM loot l
                JOIN targets t ON l.target_id = t.id
                WHERE l.loot_type = ?
                ORDER BY l.created_at DESC
            """, (loot_type,))
        else:
            cursor.execute("""
                SELECT l.*, t.ip, t.port, t.country 
                FROM loot l
                JOIN targets t ON l.target_id = t.id
                ORDER BY l.created_at DESC
            """)
        
        loot_list = []
        for row in cursor.fetchall():
            loot_dict = dict(row)
            loot_dict['data'] = json.loads(loot_dict['data'])
            loot_list.append(loot_dict)
        
        return loot_list
    
    def get_statistics(self) -> Dict:
        """
        الحصول على إحصائيات شاملة
        
        Returns:
            إحصائيات قاعدة البيانات
        """
        cursor = self.conn.cursor()
        
        stats = {}
        
        # إجمالي الأهداف
        cursor.execute("SELECT COUNT(*) as count FROM targets")
        stats["total_targets"] = cursor.fetchone()[0]
        
        # الأهداف حسب الحالة
        cursor.execute("SELECT status, COUNT(*) as count FROM targets GROUP BY status")
        stats["by_status"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # الأهداف حسب النوع
        cursor.execute("SELECT attack_type, COUNT(*) as count FROM targets GROUP BY attack_type")
        stats["by_type"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # الأهداف حسب الدولة
        cursor.execute("SELECT country, COUNT(*) as count FROM targets GROUP BY country ORDER BY count DESC LIMIT 10")
        stats["by_country"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # إجمالي الغنائم
        cursor.execute("SELECT COUNT(*) as count FROM loot")
        stats["total_loot"] = cursor.fetchone()[0]
        
        # الغنائم حسب النوع
        cursor.execute("SELECT loot_type, COUNT(*) as count FROM loot GROUP BY loot_type")
        stats["loot_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        return stats
    
    def export_to_json(self, output_file: str = None) -> str:
        """
        تصدير جميع البيانات إلى JSON
        
        Args:
            output_file: مسار ملف الإخراج
        
        Returns:
            مسار الملف المُصدَّر
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(DATA_DIR / f"export_{timestamp}.json")
        
        data = {
            "targets": self.get_all_targets(),
            "loot": self.get_all_loot(),
            "statistics": self.get_statistics(),
            "exported_at": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def export_loot_report(self, output_file: str = None) -> str:
        """
        تصدير تقرير الغنائم بتنسيق قابل للقراءة
        
        Args:
            output_file: مسار ملف الإخراج
        
        Returns:
            مسار الملف المُصدَّر
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(DATA_DIR / f"loot_report_{timestamp}.txt")
        
        stats = self.get_statistics()
        loot = self.get_all_loot()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("═" * 80 + "\n")
            f.write("تقرير غنائم رُمْح شودان\n")
            f.write(f"تاريخ التصدير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("═" * 80 + "\n\n")
            
            f.write("📊 الإحصائيات العامة:\n")
            f.write(f"   • إجمالي الأهداف: {stats['total_targets']}\n")
            f.write(f"   • الأهداف الناجحة: {stats['by_status'].get('success', 0)}\n")
            f.write(f"   • إجمالي الغنائم: {stats['total_loot']}\n\n")
            
            f.write("🌍 التوزيع الجغرافي (أعلى 10 دول):\n")
            for country, count in stats['by_country'].items():
                f.write(f"   • {country}: {count}\n")
            f.write("\n")
            
            f.write("🎯 الأهداف حسب النوع:\n")
            for attack_type, count in stats['by_type'].items():
                f.write(f"   • {attack_type}: {count}\n")
            f.write("\n")
            
            f.write("═" * 80 + "\n")
            f.write("💎 تفاصيل الغنائم:\n")
            f.write("═" * 80 + "\n\n")
            
            for item in loot:
                f.write(f"[{item['loot_type'].upper()}] {item['ip']}:{item['port']} ({item['country']})\n")
                f.write(f"   الطريقة: {item['method']}\n")
                f.write(f"   التاريخ: {item['created_at']}\n")
                
                data = item['data']
                if data.get('url'):
                    f.write(f"   الرابط: {data['url']}\n")
                if data.get('username'):
                    f.write(f"   المستخدم: {data['username']}\n")
                if data.get('password'):
                    f.write(f"   كلمة المرور: {data['password']}\n")
                if data.get('connection_string'):
                    f.write(f"   سلسلة الاتصال: {data['connection_string']}\n")
                
                f.write("\n")
        
        return output_file
    
    def search_targets(self, keyword: str) -> List[Dict]:
        """
        البحث في الأهداف
        
        Args:
            keyword: كلمة البحث
        
        Returns:
            قائمة الأهداف المطابقة
        """
        cursor = self.conn.cursor()
        
        keyword = f"%{keyword}%"
        cursor.execute("""
            SELECT * FROM targets 
            WHERE ip LIKE ? OR hostname LIKE ? OR organization LIKE ? OR country LIKE ?
            ORDER BY discovered_at DESC
        """, (keyword, keyword, keyword, keyword))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_target(self, target_id: int):
        """
        حذف هدف وغنائمه
        
        Args:
            target_id: معرف الهدف
        """
        cursor = self.conn.cursor()
        
        # حذف الغنائم أولاً
        cursor.execute("DELETE FROM loot WHERE target_id = ?", (target_id,))
        
        # حذف الهدف
        cursor.execute("DELETE FROM targets WHERE id = ?", (target_id,))
        
        self.conn.commit()
    
    def clear_all_data(self):
        """مسح جميع البيانات"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM loot")
        cursor.execute("DELETE FROM targets")
        cursor.execute("DELETE FROM statistics")
        self.conn.commit()
    
    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """تنظيف عند الحذف"""
        self.close()
