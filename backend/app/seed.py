"""Seed database with initial data."""
import asyncio
import json
from pathlib import Path
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import User, Script, Scene, Character, Achievement
from app.services.storage import get_storage


async def seed():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Script).limit(1))
        if result.scalar():
            print("Database already seeded, skipping...")
            return

        # Create achievements
        achievements = [
            Achievement(name="初次探索", description="完成你的第一个剧本", icon="🎯", condition_type="games_completed", condition_data={"count": 1}, points=10),
            Achievement(name="推理大师", description="完成10个悬疑类剧本", icon="🔍", condition_type="genre_completed", condition_data={"genre": "悬疑推理", "count": 10}, points=50),
            Achievement(name="社交达人", description="与所有NPC建立友好关系", icon="🤝", condition_type="max_relationship", condition_data={"level": "friendly"}, points=30),
            Achievement(name="完美结局", description="达成一个剧本的完美结局", icon="⭐", condition_type="ending_reached", condition_data={"ending": "good"}, points=25),
            Achievement(name="探索者", description="发现所有隐藏场景", icon="🗺️", condition_type="scenes_discovered", condition_data={"count": 10}, points=20),
        ]
        session.add_all(achievements)

        # Get existing user
        result = await session.execute(select(User).where(User.username == "testuser"))
        user = result.scalar()
        if not user:
            user = User(username="testuser", email="test@example.com", password_hash="$2b$12$dummy")
            session.add(user)
            await session.flush()

        # Create script
        script = Script(
            title="迷雾庄园",
            description="一座被迷雾笼罩的古老庄园，深夜里传来诡异的声响。你受邀前来参加一场神秘的晚宴，却发现自己陷入了一场精心设计的谋杀迷局。每个角色都有不可告人的秘密，每个房间都隐藏着关键线索。你能否在黎明到来前揭开真相？",
            genre="悬疑推理",
            difficulty="hard",
            author_id=user.id,
            cover_image="",  # Will be set after uploading
            setting={"era": "1920年代", "location": "英格兰乡间庄园", "atmosphere": "阴森恐怖、疑云密布"},
            rules={"investigation_points": 10, "trust_system": True},
            endings={"good": "找出真凶，拯救所有人", "neutral": "找到部分真相但有人牺牲", "bad": "未能找出凶手"},
            tags=["悬疑", "推理", "恐怖"],
            status="published",
        )
        session.add(script)
        await session.flush()

        # Upload cover image to storage
        storage = get_storage()
        cover_file = Path("./uploads/covers/misty-manor.png")
        if cover_file.exists():
            cover_url = await storage.save(f"scripts/{script.id}/cover.png", cover_file.read_bytes(), "image/png")
            script.cover_image = cover_url
            print(f"Cover uploaded: {cover_url}")

        # Create scenes
        scenes_data = [
            {
                "scene_key": "lobby",
                "name": "庄园大厅",
                "description": "金碧辉煌的大厅中央悬挂着一盏巨大的水晶吊灯，墙壁上挂满了历代庄园主的画像。壁炉中的火焰跳动着，投下诡异的影子。",
                "map_data": {
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
                },
                "connected_scenes": {"north": "library", "east": "dining_room", "west": "garden"},
                "sort_order": 1,
            },
            {
                "scene_key": "library",
                "name": "庄园图书馆",
                "description": "幽暗的图书馆里弥漫着旧书和皮革的味道。高耸的书架直达天花板，角落里有一张古老的写字台，上面放着一本打开的日记。",
                "map_data": {
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
                },
                "connected_scenes": {"south": "lobby"},
                "sort_order": 2,
            },
            {
                "scene_key": "dining_room",
                "name": "庄园餐厅",
                "description": "长长的橡木餐桌上摆放着精美的银质餐具，水晶杯中残留着暗红色的液体。餐厅尽头的门通向厨房，空气中弥漫着一种奇怪的气味。",
                "map_data": {
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
                },
                "connected_scenes": {"west": "lobby", "north": "kitchen"},
                "sort_order": 3,
            },
            {
                "scene_key": "garden",
                "name": "庄园花园",
                "description": "月光下的花园显得格外阴森。枯萎的玫瑰丛中似乎有什么东西在移动，远处的喷泉早已干涸，但你能听到水滴的声音...",
                "map_data": {
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
                },
                "connected_scenes": {"east": "lobby"},
                "sort_order": 4,
            },
        ]
        for sd in scenes_data:
            scene = Scene(script_id=script.id, **sd)
            session.add(scene)

        # Create characters
        characters_data = [
            {
                "character_key": "butler",
                "name": "管家威廉",
                "display_name": "威廉",
                "role_type": "npc",
                "appearance": "身材高大，穿着整洁的黑色燕尾服，银白色的头发梳得一丝不苟。眼神深邃，似乎隐藏着无数秘密。",
                "personality": {"traits": ["沉稳", "神秘", "忠诚"], "mbti": "ISTJ"},
                "background": "在庄园服务了40年，见证了庄园的兴衰。据说他知道庄园所有的秘密，但从不对外人透露。",
                "secrets": {"secret": "知道前任庄园主死亡的真相", "trust_threshold": 80},
                "dialogue_style": "说话简洁有力，常用敬语，偶尔会意味深长地停顿。",
                "sort_order": 1,
            },
            {
                "character_key": "lady_margaret",
                "name": "玛格丽特夫人",
                "display_name": "玛格丽特",
                "role_type": "npc",
                "appearance": "优雅的中年女性，穿着华丽的晚礼服，颈间戴着璀璨的钻石项链。眼神中带着一丝忧郁。",
                "personality": {"traits": ["优雅", "忧郁", "聪慧"], "mbti": "INFJ"},
                "background": "庄园主人的遗孀，据说她的丈夫在三年前的一个雨夜神秘失踪。她很少离开庄园，整日沉浸在回忆中。",
                "secrets": {"secret": "丈夫失踪当晚她听到了什么", "trust_threshold": 60},
                "dialogue_style": "说话轻柔，喜欢引用诗句，有时会突然陷入沉思。",
                "sort_order": 2,
            },
            {
                "character_key": "doctor_holmes",
                "name": "福尔摩斯医生",
                "display_name": "医生",
                "role_type": "npc",
                "appearance": "戴着金丝眼镜的中年男子，总是随身携带一个黑色医疗箱。手指修长，动作精准。",
                "personality": {"traits": ["理性", "观察力强", "有些神经质"], "mbti": "INTP"},
                "background": "来自伦敦的医生，受邀来庄园为玛格丽特夫人看病。他对推理有着浓厚的兴趣，似乎在调查什么。",
                "secrets": {"secret": "他不是真正的医生", "trust_threshold": 70},
                "dialogue_style": "喜欢用专业术语，说话快速，经常打断别人。",
                "sort_order": 3,
            },
        ]
        for cd in characters_data:
            char = Character(script_id=script.id, **cd)
            session.add(char)

        await session.commit()
        print("Database seeded successfully!")
        print(f"Created script: {script.title}")
        print(f"Created {len(scenes_data)} scenes")
        print(f"Created {len(characters_data)} characters")
        print(f"Created {len(achievements)} achievements")


if __name__ == "__main__":
    asyncio.run(seed())
