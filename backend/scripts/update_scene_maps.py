"""Update existing scene map_data with complete investigation data."""
import asyncio
import json
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import Scene


async def update_scenes():
    async with AsyncSessionLocal() as session:
        # Lobby scene
        lobby_map = {
            "width": 1920,
            "height": 1080,
            "grid_size": 32,
            "tiles": [[1,1,1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,0,0,1],[1,0,2,0,0,0,2,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,0,0,0,3,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1,1,1]],
            "walkable_areas": [
                {"id": "lobby_main", "name": "大厅主区域", "polygon": [[120,120],[1800,120],[1800,960],[120,960]]}
            ],
            "obstacles": [
                {"id": "chandelier", "name": "水晶吊灯", "polygon": [[800,200],[1120,200],[1120,350],[800,350]], "is_solid": True},
                {"id": "fireplace", "name": "壁炉", "polygon": [[800,800],[1120,800],[1120,960],[800,960]], "is_solid": True}
            ],
            "spawn_points": [
                {"id": "lobby_entrance", "name": "大厅入口", "position": [960,900], "is_default": True},
                {"id": "lobby_center", "name": "大厅中央", "position": [960,540], "is_default": False}
            ],
            "interactable_points": [
                {
                    "id": "butler_william",
                    "name": "管家威廉",
                    "type": "npc",
                    "position": [500,500],
                    "icon": "👤",
                    "description": "身材高大的老管家，银白色的头发梳得一丝不苟。",
                    "actions": ["examine", "talk"],
                    "conditions": {},
                    "npc_id": "butler",
                    "investigation": {
                        "clue_text": "管家的袖口有一丝暗红色的痕迹，像是干涸的血迹。他注意到你的目光，迅速将手藏到了身后。",
                        "required_flags": [],
                        "revealed_flags": ["butler_blood_clue"]
                    }
                },
                {
                    "id": "lobby_exit",
                    "name": "庄园大门",
                    "type": "exit",
                    "position": [960,100],
                    "icon": "🚪",
                    "description": "厚重的橡木大门，通向庄园外的迷雾。",
                    "actions": ["examine", "enter"],
                    "conditions": {},
                    "target_scene": "garden",
                    "target_position": [960,900]
                },
                {
                    "id": "portrait_wall",
                    "name": "画像墙",
                    "type": "object",
                    "position": [200,300],
                    "icon": "🖼️",
                    "description": "墙上挂满了历代庄园主的画像，其中一幅画像的眼睛似乎在注视着你。",
                    "actions": ["examine", "touch"],
                    "conditions": {},
                    "investigation": {
                        "clue_text": "你仔细观察画像，发现其中一幅画像背后似乎藏着什么东西。移开画像，你发现了一封泛黄的信件。",
                        "required_flags": [],
                        "revealed_flags": ["secret_letter_found"]
                    }
                }
            ]
        }

        # Library scene
        library_map = {
            "width": 1600,
            "height": 900,
            "grid_size": 32,
            "tiles": [[1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,1],[1,0,2,0,0,2,0,1],[1,0,0,0,3,0,0,1],[1,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1]],
            "walkable_areas": [
                {"id": "library_main", "name": "图书馆主区域", "polygon": [[100,100],[1500,100],[1500,800],[100,800]]}
            ],
            "obstacles": [
                {"id": "bookshelves", "name": "书架", "polygon": [[100,100],[300,100],[300,800],[100,800]], "is_solid": True},
                {"id": "desk", "name": "写字台", "polygon": [[700,400],[900,400],[900,600],[700,600]], "is_solid": True}
            ],
            "spawn_points": [
                {"id": "library_entrance", "name": "图书馆入口", "position": [800,800], "is_default": True}
            ],
            "interactable_points": [
                {
                    "id": "diary",
                    "name": "打开的日记",
                    "type": "item",
                    "position": [800,500],
                    "icon": "📖",
                    "description": "一本古老的日记，纸页已经泛黄。",
                    "actions": ["examine", "pick_up"],
                    "conditions": {},
                    "investigation": {
                        "clue_text": "日记中记载了庄园主失踪前最后几天的异常行为。他反复提到'地下室的秘密'和'那个不能说的名字'。",
                        "required_flags": [],
                        "revealed_flags": ["diary_read"]
                    }
                },
                {
                    "id": "lady_margaret",
                    "name": "玛格丽特夫人",
                    "type": "npc",
                    "position": [1200,400],
                    "icon": "👤",
                    "description": "优雅的中年女性，颈间戴着璀璨的钻石项链。",
                    "actions": ["examine", "talk"],
                    "conditions": {},
                    "npc_id": "lady_margaret",
                    "investigation": {
                        "clue_text": "玛格丽特夫人的眼神闪烁不定，当你提到她丈夫时，她的手不自觉地摸向了颈间的项链。",
                        "required_flags": [],
                        "revealed_flags": ["margaret_nervous"]
                    }
                }
            ]
        }

        # Dining room scene
        dining_map = {
            "width": 1920,
            "height": 900,
            "grid_size": 32,
            "tiles": [[1,1,1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,0,0,1],[1,0,0,3,0,0,0,0,0,1],[1,0,0,0,0,0,2,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1,1,1]],
            "walkable_areas": [
                {"id": "dining_main", "name": "餐厅主区域", "polygon": [[120,120],[1800,120],[1800,780],[120,780]]}
            ],
            "obstacles": [
                {"id": "dining_table", "name": "餐桌", "polygon": [[400,300],[1520,300],[1520,500],[400,500]], "is_solid": True}
            ],
            "spawn_points": [
                {"id": "dining_entrance", "name": "餐厅入口", "position": [960,800], "is_default": True}
            ],
            "interactable_points": [
                {
                    "id": "wine_glasses",
                    "name": "水晶杯",
                    "type": "object",
                    "position": [960,400],
                    "icon": "🍷",
                    "description": "几个水晶杯，里面残留着暗红色的液体。",
                    "actions": ["examine", "search"],
                    "conditions": {},
                    "investigation": {
                        "clue_text": "你闻了闻杯中的液体，不是红酒，而是一股刺鼻的化学药剂味。杯底还残留着一些白色粉末。",
                        "required_flags": [],
                        "revealed_flags": ["poison_evidence"]
                    }
                },
                {
                    "id": "doctor_holmes",
                    "name": "福尔摩斯医生",
                    "type": "npc",
                    "position": [1400,300],
                    "icon": "👤",
                    "description": "戴着金丝眼镜的中年男子，总是随身携带一个黑色医疗箱。",
                    "actions": ["examine", "talk"],
                    "conditions": {},
                    "npc_id": "doctor_holmes",
                    "investigation": {
                        "clue_text": "医生的医疗箱没有完全关紧，你瞥见里面除了医疗器械，还有一把手枪和几张伪造的身份证件。",
                        "required_flags": [],
                        "revealed_flags": ["doctor_fake_identity"]
                    }
                }
            ]
        }

        # Garden scene
        garden_map = {
            "width": 1920,
            "height": 1080,
            "grid_size": 32,
            "tiles": [[1,1,1,1,1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,0,0,0,0,1],[1,0,4,0,0,0,0,0,4,0,0,1],[1,0,0,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,3,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1,1,1,1,1]],
            "walkable_areas": [
                {"id": "garden_paths", "name": "花园小径", "polygon": [[120,120],[1800,120],[1800,960],[120,960]]}
            ],
            "obstacles": [
                {"id": "fountain", "name": "干涸的喷泉", "polygon": [[800,400],[1120,400],[1120,680],[800,680]], "is_solid": True},
                {"id": "rose_bushes", "name": "玫瑰丛", "polygon": [[200,200],[400,200],[400,400],[200,400]], "is_solid": True}
            ],
            "spawn_points": [
                {"id": "garden_gate", "name": "花园大门", "position": [960,900], "is_default": True}
            ],
            "interactable_points": [
                {
                    "id": "fountain_statue",
                    "name": "喷泉雕像",
                    "type": "object",
                    "position": [960,540],
                    "icon": "⛲",
                    "description": "一座天使雕像，底座上刻着模糊的文字。",
                    "actions": ["examine", "touch"],
                    "conditions": {},
                    "investigation": {
                        "clue_text": "你转动雕像底座，发现下面藏着一把生锈的钥匙。钥匙上刻着'地下室'三个字。",
                        "required_flags": [],
                        "revealed_flags": ["basement_key_found"]
                    }
                },
                {
                    "id": "strange_sound",
                    "name": "奇怪的声响",
                    "type": "event",
                    "position": [300,300],
                    "icon": "👂",
                    "description": "玫瑰丛深处传来窸窸窣窣的声音。",
                    "actions": ["examine", "search"],
                    "conditions": {},
                    "investigation": {
                        "clue_text": "你拨开玫瑰丛，发现了一只被遗弃的怀表。表盘停在午夜12点，背面刻着庄园主的名字。",
                        "required_flags": [],
                        "revealed_flags": ["pocket_watch_found"]
                    }
                }
            ]
        }

        # Update scenes
        scene_maps = {
            "lobby": lobby_map,
            "library": library_map,
            "dining_room": dining_map,
            "garden": garden_map,
        }

        for scene_key, map_data in scene_maps.items():
            result = await session.execute(
                select(Scene).where(Scene.scene_key == scene_key)
            )
            scene = result.scalar_one_or_none()
            if scene:
                scene.map_data = map_data
                print(f"Updated scene: {scene_key}")
            else:
                print(f"Scene not found: {scene_key}")

        await session.commit()
        print("Scene map_data updated successfully!")


if __name__ == "__main__":
    asyncio.run(update_scenes())
