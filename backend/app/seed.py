"""Seed database with initial data."""
import asyncio
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
            Achievement(name="完美结局", description="达成一个剧本的完美结局", icon="⭐", condition_type="ending_reached", condition_data={"ending": "perfect"}, points=25),
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

        # Create script with enhanced rules and endings
        script = Script(
            title="迷雾庄园",
            description="一座被迷雾笼罩的古老庄园，深夜里传来诡异的声响。你受邀前来调查布莱克伍德勋爵三年前的神秘失踪。每个角色都有不可告人的秘密，每个房间都隐藏着关键线索。真凶就隐藏在这些看似无辜的面孔之中——你能否在黎明到来前揭开真相，还是会被迷雾永远吞噬？",
            genre="悬疑推理",
            difficulty="hard",
            author_id=user.id,
            cover_image="",
            setting={
                "era": "1920年代",
                "location": "英格兰乡间庄园",
                "atmosphere": "阴森恐怖、疑云密布",
                "world": "战后英格兰，社会动荡，走私猖獗",
                "premise": "布莱克伍德勋爵三年前在一个雨夜神秘失踪，你作为受雇的侦探前来调查真相",
            },
            rules={
                "investigation_points": 10,
                "trust_system": True,
                "accusation_enabled": True,
                "accusation_rules": {
                    "min_evidence_flags": 3,
                    "correct_accusation_target": "butler",
                    "accusation_keyword": "指控",
                    "wrong_accusation_endings": ["bad", "tragic"],
                    "correct_accusation_endings": ["good", "perfect"],
                },
                "win_conditions": {
                    "type": "accusation",
                    "target": "butler",
                    "required_flags_for_perfect": [
                        "basement_body_found",
                        "butler_motive_revealed",
                        "poison_evidence",
                        "secret_letter_found",
                    ],
                    "required_flags_for_good": ["basement_body_found", "butler_motive_revealed"],
                },
                "lose_conditions": {
                    "wrong_accusation": True,
                    "accuse_innocent": "bad",
                },
            },
            endings={
                "perfect": "在铁证如山面前，威廉终于崩溃认罪。你不仅找出了真凶，还揭露了庄园长达数十年的走私罪行，所有无辜者得以平安。布莱克伍德勋爵的冤屈终于昭雪。",
                "good": "你成功指认威廉为凶手，虽然部分证据不够充分，但你的推理说服了在场所有人。真相大白，但一些秘密永远埋藏在了迷雾中。",
                "neutral": "你找到了部分真相，但未能收集到足够证据指认真凶。威廉继续隐藏在管家的身份之下，而你的疑虑将永远无法得到证实。",
                "bad": "你错误地指控了无辜的人，真凶威廉趁机销毁了剩余证据。无辜者蒙冤，真相被永远掩埋在迷雾庄园的阴影中。",
                "tragic": "你的错误指控引发了连锁反应，真凶在混乱中再次下手。当黎明到来时，庄园中又多了一个永远沉默的灵魂。",
            },
            tags=["悬疑", "推理", "恐怖", "密室"],
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

        # Upload scene background images
        scene_bg_map = {
            "lobby": "lobby_bg.png",
            "library": "library_bg.png",
            "dining_room": "dining_bg.png",
            "garden": "garden_bg.png",
            "kitchen": "kitchen_bg.png",
            "basement": "basement_bg.png",
            "study": "study_bg.png",
        }
        scene_bg_urls = {}
        for scene_key, bg_file_name in scene_bg_map.items():
            bg_file = Path(f"./uploads/scenes/{bg_file_name}")
            if bg_file.exists():
                url = await storage.save(f"scripts/{script.id}/scenes/{scene_key}/bg.png", bg_file.read_bytes(), "image/png")
                scene_bg_urls[scene_key] = url
                print(f"Scene {scene_key} background uploaded: {url}")

        # Upload character avatars
        char_avatar_map = {
            "butler": "butler_avatar.png",
            "lady_margaret": "lady_margaret_avatar.png",
            "doctor_holmes": "doctor_holmes_avatar.png",
            "cook_martha": "cook_avatar.png",
            "young_master": "young_master_avatar.png",
        }
        char_avatar_urls = {}
        for char_key, avatar_file_name in char_avatar_map.items():
            avatar_file = Path(f"./uploads/characters/{avatar_file_name}")
            if avatar_file.exists():
                url = await storage.save(f"scripts/{script.id}/characters/{char_key}/avatar.png", avatar_file.read_bytes(), "image/png")
                char_avatar_urls[char_key] = url
                print(f"Character {char_key} avatar uploaded: {url}")

        # Create scenes (7 scenes)
        scenes_data = [
            # Scene 1: Lobby
            {
                "scene_key": "lobby",
                "name": "庄园大厅",
                "description": "金碧辉煌的大厅中央悬挂着一盏巨大的水晶吊灯，墙壁上挂满了历代庄园主的画像。壁炉中的火焰跳动着，投下诡异的影子。空气中弥漫着陈旧的气息，仿佛时间在这里停滞了。",
                "background_image": scene_bg_urls.get("lobby", ""),
                "map_data": {
                    "width": 1920,
                    "height": 1080,
                    "grid_size": 32,
                    "tiles": [[1,1,1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,0,0,1],[1,0,2,0,0,0,2,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,0,0,0,3,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1,1,1]],
                    "walkable_areas": [{"id": "lobby_main", "name": "大厅主区域", "polygon": [[120,120],[1800,120],[1800,960],[120,960]]}],
                    "obstacles": [
                        {"id": "chandelier", "name": "水晶吊灯", "polygon": [[800,200],[1120,200],[1120,350],[800,350]], "is_solid": True},
                        {"id": "fireplace", "name": "壁炉", "polygon": [[800,800],[1120,800],[1120,960],[800,960]], "is_solid": True},
                    ],
                    "spawn_points": [{"id": "lobby_entrance", "name": "大厅入口", "position": [960,900], "is_default": True}],
                    "interactable_points": [
                        {
                            "id": "butler_william",
                            "name": "管家威廉",
                            "type": "npc",
                            "position": [500,500],
                            "icon": "/uploads/characters/butler_avatar.png",
                            "description": "身材高大的老管家，银白色的头发梳得一丝不苟。他的双手总是微微颤抖，仿佛在极力控制着什么。",
                            "actions": ["examine", "talk"],
                            "conditions": {},
                            "npc_id": "butler",
                            "investigation": {
                                "clue_text": "管家的袖口有一丝暗红色的痕迹，像是干涸的血迹。他注意到你的目光，迅速将手藏到了身后，眼神中闪过一丝慌乱。",
                                "required_flags": [],
                                "revealed_flags": ["butler_blood_clue"],
                            },
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
                                "clue_text": "你仔细观察画像，发现其中一幅画像背后似乎藏着什么东西。移开画像，你发现了一封泛黄的信件——是布莱克伍德勋爵写给伦敦律师的信，提到'地下室的走私活动'和'必须向当局报告'。",
                                "required_flags": [],
                                "revealed_flags": ["secret_letter_found"],
                            },
                        },
                        {
                            "id": "grandfather_clock",
                            "name": "落地钟",
                            "type": "object",
                            "position": [1600,400],
                            "icon": "🕰️",
                            "description": "一座古老的落地钟，钟面显示的时间永远停在午夜十二点。",
                            "actions": ["examine"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "钟的指针卡在午夜十二点——正是三年前那个雨夜，布莱克伍德勋爵失踪的时间。钟的机械结构似乎被人故意破坏了。",
                                "required_flags": [],
                                "revealed_flags": ["clock_stopped_midnight"],
                            },
                        },
                        {
                            "id": "lobby_exit_north",
                            "name": "通往图书馆的门",
                            "type": "exit",
                            "position": [960,100],
                            "icon": "🚪",
                            "description": "一扇厚重的橡木门，通向图书馆。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "library",
                            "target_position": [960,800],
                        },
                        {
                            "id": "lobby_exit_east",
                            "name": "通往餐厅的门",
                            "type": "exit",
                            "position": [1800,540],
                            "icon": "🚪",
                            "description": "通向餐厅的双开门，隐约能闻到食物的香气。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "dining_room",
                            "target_position": [200,540],
                        },
                        {
                            "id": "lobby_exit_west",
                            "name": "通往花园的门",
                            "type": "exit",
                            "position": [120,540],
                            "icon": "🚪",
                            "description": "通向花园的玻璃门，外面是浓重的迷雾。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "garden",
                            "target_position": [1800,540],
                        },
                        {
                            "id": "lobby_exit_south",
                            "name": "通往书房的门",
                            "type": "exit",
                            "position": [960,1000],
                            "icon": "🚪",
                            "description": "一扇较小的门，通向勋爵的私人书房。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "study",
                            "target_position": [960,200],
                        },
                    ],
                },
                "connected_scenes": {"north": "library", "east": "dining_room", "west": "garden", "south": "study"},
                "sort_order": 1,
            },
            # Scene 2: Library
            {
                "scene_key": "library",
                "name": "庄园图书馆",
                "description": "幽暗的图书馆里弥漫着旧书和皮革的味道。高耸的书架直达天花板，角落里有一张古老的写字台，上面放着一本打开的日记。壁炉旁的扶手椅上似乎还残留着余温。",
                "background_image": scene_bg_urls.get("library", ""),
                "map_data": {
                    "width": 1600,
                    "height": 900,
                    "grid_size": 32,
                    "tiles": [[1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,1],[1,0,2,0,0,2,0,1],[1,0,0,0,3,0,0,1],[1,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1]],
                    "walkable_areas": [{"id": "library_main", "name": "图书馆主区域", "polygon": [[100,100],[1500,100],[1500,800],[100,800]]}],
                    "obstacles": [
                        {"id": "bookshelves_left", "name": "书架", "polygon": [[100,100],[300,100],[300,800],[100,800]], "is_solid": True},
                        {"id": "desk", "name": "写字台", "polygon": [[700,400],[900,400],[900,600],[700,600]], "is_solid": True},
                    ],
                    "spawn_points": [{"id": "library_entrance", "name": "图书馆入口", "position": [800,800], "is_default": True}],
                    "interactable_points": [
                        {
                            "id": "diary",
                            "name": "打开的日记",
                            "type": "item",
                            "position": [800,500],
                            "icon": "📖",
                            "description": "一本古老的日记，纸页已经泛黄。封面上写着'布莱克伍德'。",
                            "actions": ["examine", "read"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "日记中记载了勋爵失踪前最后几天的异常。他反复提到'威廉深夜出入地下室'、'地下室的门总是锁着'、'必须查清他在隐藏什么'。最后一页写着：'今晚我要当面质问他。如果他真的在做什么违法的事，我必须阻止。'",
                                "required_flags": [],
                                "revealed_flags": ["diary_read"],
                            },
                        },
                        {
                            "id": "lady_margaret",
                            "name": "玛格丽特夫人",
                            "type": "npc",
                            "position": [1200,400],
                            "icon": "/uploads/characters/lady_margaret_avatar.png",
                            "description": "优雅的中年女性，穿着华丽的黑色晚礼服，颈间戴着璀璨的钻石项链。她的眼神中带着深深的忧郁。",
                            "actions": ["examine", "talk"],
                            "conditions": {},
                            "npc_id": "lady_margaret",
                            "investigation": {
                                "clue_text": "玛格丽特夫人的眼神闪烁不定，当你提到她丈夫时，她的手不自觉地摸向了颈间的项链。她似乎在隐藏什么，但那更像是关于丈夫打算离开她的秘密，而非谋杀。",
                                "required_flags": [],
                                "revealed_flags": ["margaret_nervous"],
                            },
                        },
                        {
                            "id": "hidden_compartment",
                            "name": "写字台抽屉",
                            "type": "object",
                            "position": [800,550],
                            "icon": "🗄️",
                            "description": "写字台有一个隐蔽的暗格，需要特定的机关才能打开。",
                            "actions": ["examine", "search"],
                            "conditions": {"examine": [{"type": "flag", "flag": "diary_read", "value": True}]},
                            "investigation": {
                                "clue_text": "你想起日记中提到的机关，按下抽屉底部的暗扣。暗格弹开，里面是一张旧照片——照片上威廉站在庄园码头的货物箱旁，表情阴沉。照片背面写着'1920年，最后一批货'。",
                                "required_flags": ["diary_read"],
                                "revealed_flags": ["compartment_photo"],
                            },
                        },
                        {
                            "id": "library_exit_south",
                            "name": "返回大厅",
                            "type": "exit",
                            "position": [800,850],
                            "icon": "🚪",
                            "description": "返回庄园大厅。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "lobby",
                            "target_position": [960,200],
                        },
                        {
                            "id": "library_exit_east",
                            "name": "通往书房",
                            "type": "exit",
                            "position": [1500,450],
                            "icon": "🚪",
                            "description": "一扇连接书房的小门。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "study",
                            "target_position": [200,450],
                        },
                    ],
                },
                "connected_scenes": {"south": "lobby", "east": "study"},
                "sort_order": 2,
            },
            # Scene 3: Dining Room
            {
                "scene_key": "dining_room",
                "name": "庄园餐厅",
                "description": "长长的橡木餐桌上摆放着精美的银质餐具，水晶杯中残留着暗红色的液体。餐厅尽头的门通向厨房，空气中弥漫着一种奇怪的气味——像是某种化学药剂。",
                "background_image": scene_bg_urls.get("dining_room", ""),
                "map_data": {
                    "width": 1920,
                    "height": 900,
                    "grid_size": 32,
                    "tiles": [[1,1,1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,0,0,1],[1,0,0,3,0,0,0,0,0,1],[1,0,0,0,0,0,2,0,0,1],[1,0,0,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1,1,1]],
                    "walkable_areas": [{"id": "dining_main", "name": "餐厅主区域", "polygon": [[120,120],[1800,120],[1800,780],[120,780]]}],
                    "obstacles": [{"id": "dining_table", "name": "餐桌", "polygon": [[400,300],[1520,300],[1520,500],[400,500]], "is_solid": True}],
                    "spawn_points": [{"id": "dining_entrance", "name": "餐厅入口", "position": [200,540], "is_default": True}],
                    "interactable_points": [
                        {
                            "id": "wine_glasses",
                            "name": "水晶杯",
                            "type": "object",
                            "position": [960,400],
                            "icon": "🍷",
                            "description": "几个水晶杯，里面残留着暗红色的液体。这些杯子似乎很久没有人动过了。",
                            "actions": ["examine", "smell"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "你闻了闻杯中的液体，不是红酒，而是一股刺鼻的化学药剂味。杯底还残留着一些白色粉末。这很可能是一种罕见的毒药——只有长期在庄园工作的人才能接触到。",
                                "required_flags": [],
                                "revealed_flags": ["poison_evidence"],
                            },
                        },
                        {
                            "id": "doctor_holmes",
                            "name": "福尔摩斯医生",
                            "type": "npc",
                            "position": [1400,300],
                            "icon": "/uploads/characters/doctor_holmes_avatar.png",
                            "description": "戴着金丝眼镜的中年男子，总是随身携带一个黑色医疗箱。他的目光锐利，似乎在观察着每一个人。",
                            "actions": ["examine", "talk"],
                            "conditions": {},
                            "npc_id": "doctor_holmes",
                            "investigation": {
                                "clue_text": "医生的医疗箱没有完全关紧，你瞥见里面除了医疗器械，还有一把手枪和几张伪造的身份证件。他似乎不是真正的医生，而是一个私家侦探。",
                                "required_flags": [],
                                "revealed_flags": ["doctor_fake_identity"],
                            },
                        },
                        {
                            "id": "dining_table_drawer",
                            "name": "餐桌抽屉",
                            "type": "object",
                            "position": [500,400],
                            "icon": "🗄️",
                            "description": "餐桌下方的抽屉，似乎放着一些文件。",
                            "actions": ["examine", "open"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "抽屉里是一份三年前的晚宴宾客名单。那晚的客人包括：玛格丽特夫人、福尔摩斯医生、管家威廉、厨师玛莎。而少爷爱德华的名字被划掉了，旁边写着'未出席'。",
                                "required_flags": [],
                                "revealed_flags": ["dinner_guest_list"],
                            },
                        },
                        {
                            "id": "dining_exit_west",
                            "name": "返回大厅",
                            "type": "exit",
                            "position": [120,540],
                            "icon": "🚪",
                            "description": "返回庄园大厅。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "lobby",
                            "target_position": [1700,540],
                        },
                        {
                            "id": "dining_exit_north",
                            "name": "通往厨房",
                            "type": "exit",
                            "position": [960,100],
                            "icon": "🚪",
                            "description": "通向厨房的门，能听到里面传来的声音。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "kitchen",
                            "target_position": [960,800],
                        },
                    ],
                },
                "connected_scenes": {"west": "lobby", "north": "kitchen"},
                "sort_order": 3,
            },
            # Scene 4: Garden
            {
                "scene_key": "garden",
                "name": "庄园花园",
                "description": "月光下的花园显得格外阴森。枯萎的玫瑰丛中似乎有什么东西在移动，远处的喷泉早已干涸，但你能听到水滴的声音。花园深处有一扇生锈的铁门，通向庄园的地下室入口。",
                "background_image": scene_bg_urls.get("garden", ""),
                "map_data": {
                    "width": 1920,
                    "height": 1080,
                    "grid_size": 32,
                    "tiles": [[1,1,1,1,1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,0,0,0,0,1],[1,0,4,0,0,0,0,0,4,0,0,1],[1,0,0,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,3,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,0,0,1],[1,0,0,0,0,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1,1,1,1,1]],
                    "walkable_areas": [{"id": "garden_paths", "name": "花园小径", "polygon": [[120,120],[1800,120],[1800,960],[120,960]]}],
                    "obstacles": [
                        {"id": "fountain", "name": "干涸的喷泉", "polygon": [[800,400],[1120,400],[1120,680],[800,680]], "is_solid": True},
                        {"id": "rose_bushes", "name": "玫瑰丛", "polygon": [[200,200],[400,200],[400,400],[200,400]], "is_solid": True},
                    ],
                    "spawn_points": [{"id": "garden_gate", "name": "花园大门", "position": [1800,540], "is_default": True}],
                    "interactable_points": [
                        {
                            "id": "fountain_statue",
                            "name": "喷泉雕像",
                            "type": "object",
                            "position": [960,540],
                            "icon": "⛲",
                            "description": "一座天使雕像，底座上刻着模糊的文字。雕像的底座似乎可以转动。",
                            "actions": ["examine", "turn"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "你转动雕像底座，发现下面藏着一把生锈的钥匙。钥匙上刻着'地下室'三个字。这把钥匙看起来很久没有人用过了。",
                                "required_flags": [],
                                "revealed_flags": ["basement_key_found"],
                            },
                        },
                        {
                            "id": "strange_sound",
                            "name": "玫瑰丛深处",
                            "type": "event",
                            "position": [300,300],
                            "icon": "👂",
                            "description": "玫瑰丛深处传来窸窸窣窣的声音，似乎有什么东西被埋在那里。",
                            "actions": ["examine", "search"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "你拨开玫瑰丛，发现了一只被遗弃的怀表。表盘停在午夜12点，背面刻着'布莱克伍德勋爵'。这块表很可能是威廉故意丢弃的，用来制造勋爵在花园失踪的假象。",
                                "required_flags": [],
                                "revealed_flags": ["pocket_watch_found"],
                            },
                        },
                        {
                            "id": "garden_shed",
                            "name": "园艺工具棚",
                            "type": "object",
                            "position": [1600,800],
                            "icon": "🏚️",
                            "description": "一个破旧的工具棚，里面放着各种园艺工具。",
                            "actions": ["examine", "search"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "工具棚里的铁锹和铲子上有新鲜的泥土痕迹，似乎最近被使用过。但花园里的植物都已经枯萎了，谁会在深夜使用这些工具？",
                                "required_flags": [],
                                "revealed_flags": ["shed_digging_tools"],
                            },
                        },
                        {
                            "id": "garden_exit_east",
                            "name": "返回大厅",
                            "type": "exit",
                            "position": [1800,540],
                            "icon": "🚪",
                            "description": "返回庄园大厅。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "lobby",
                            "target_position": [200,540],
                        },
                        {
                            "id": "basement_entrance",
                            "name": "地下室入口",
                            "type": "exit",
                            "position": [960,1000],
                            "icon": "🚪",
                            "description": "一扇生锈的铁门，通向庄园的地下室。门上挂着一把生锈的锁。",
                            "actions": ["enter", "examine"],
                            "conditions": {"enter": [{"type": "flag", "flag": "basement_key_found", "value": True}]},
                            "target_scene": "basement",
                            "target_position": [960,900],
                        },
                    ],
                },
                "connected_scenes": {"east": "lobby", "south": "basement"},
                "sort_order": 4,
            },
            # Scene 5: Kitchen (NEW)
            {
                "scene_key": "kitchen",
                "name": "庄园厨房",
                "description": "弥漫着香料和面粉气味的厨房，铜锅在炉火上发出轻微的咕嘟声。角落里的刀架上少了一把刀，厨师玛莎正在忙碌地准备着什么，时不时紧张地看向门口。",
                "background_image": scene_bg_urls.get("kitchen", ""),
                "map_data": {
                    "width": 1200,
                    "height": 800,
                    "grid_size": 32,
                    "tiles": [[1,1,1,1,1,1,1],[1,0,0,0,0,0,1],[1,0,2,0,3,0,1],[1,0,0,0,0,0,1],[1,1,1,1,1,1,1]],
                    "walkable_areas": [{"id": "kitchen_main", "name": "厨房主区域", "polygon": [[100,100],[1100,100],[1100,700],[100,700]]}],
                    "obstacles": [
                        {"id": "stove", "name": "炉灶", "polygon": [[800,200],[1000,200],[1000,400],[800,400]], "is_solid": True},
                        {"id": "prep_table", "name": "料理台", "polygon": [[400,300],[600,300],[600,500],[400,500]], "is_solid": True},
                    ],
                    "spawn_points": [{"id": "kitchen_entrance", "name": "厨房入口", "position": [960,700], "is_default": True}],
                    "interactable_points": [
                        {
                            "id": "cook_martha",
                            "name": "厨师玛莎",
                            "type": "npc",
                            "position": [500,400],
                            "icon": "/uploads/characters/cook_avatar.png",
                            "description": "身材圆润的中年妇女，围着沾满油渍的围裙，脸上总是挂着和善的微笑，但眼神中偶尔闪过一丝忧虑。",
                            "actions": ["examine", "talk"],
                            "conditions": {},
                            "npc_id": "cook_martha",
                            "investigation": {
                                "clue_text": "玛莎压低声音告诉你：'那晚...我起来找水喝，看到威廉先生从地下室出来，手里拿着一个沉重的袋子。他看起来很紧张，还警告我不要多管闲事。'她是关键证人！",
                                "required_flags": [],
                                "revealed_flags": ["cook_testimony"],
                            },
                        },
                        {
                            "id": "knife_rack",
                            "name": "刀架",
                            "type": "object",
                            "position": [200,300],
                            "icon": "🔪",
                            "description": "一个木制刀架，上面插着几把厨刀，但有一个空位。",
                            "actions": ["examine"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "刀架上少了一把切肉刀。玛莎解释说那把刀早就坏了，被她扔掉了。但这似乎是一个红鲱鱼——勋爵并非死于刀伤。",
                                "required_flags": [],
                                "revealed_flags": ["kitchen_knife_missing"],
                            },
                        },
                        {
                            "id": "recipe_book",
                            "name": "食谱本",
                            "type": "item",
                            "position": [300,500],
                            "icon": "📔",
                            "description": "一本破旧的食谱本，里面夹着一些纸条。",
                            "actions": ["examine", "read"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "食谱本里夹着一张纸条，上面写着玛莎的八卦：'夫人最近和那个医生走得很近，不知道老爷知不知道...'但这似乎只是无根据的流言。",
                                "required_flags": [],
                                "revealed_flags": ["cook_hearsay"],
                            },
                        },
                        {
                            "id": "kitchen_exit_south",
                            "name": "返回餐厅",
                            "type": "exit",
                            "position": [960,750],
                            "icon": "🚪",
                            "description": "返回餐厅。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "dining_room",
                            "target_position": [960,200],
                        },
                    ],
                },
                "connected_scenes": {"south": "dining_room"},
                "sort_order": 5,
            },
            # Scene 6: Basement (NEW - requires key)
            {
                "scene_key": "basement",
                "name": "庄园地下室",
                "description": "阴暗潮湿的地下室，空气中弥漫着霉味和一种说不出的腐朽气息。摇曳的烛光照亮了角落里堆积的木箱，地面上有拖拽的痕迹。这里隐藏着庄园最黑暗的秘密。",
                "background_image": scene_bg_urls.get("basement", ""),
                "map_data": {
                    "width": 1400,
                    "height": 900,
                    "grid_size": 32,
                    "tiles": [[1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,1],[1,0,2,0,3,0,0,1],[1,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1]],
                    "walkable_areas": [{"id": "basement_main", "name": "地下室主区域", "polygon": [[100,100],[1300,100],[1300,800],[100,800]]}],
                    "obstacles": [
                        {"id": "crates", "name": "木箱堆", "polygon": [[100,100],[400,100],[400,400],[100,400]], "is_solid": True},
                        {"id": "pillar", "name": "石柱", "polygon": [[700,400],[800,400],[800,500],[700,500]], "is_solid": True},
                    ],
                    "spawn_points": [{"id": "basement_entrance", "name": "地下室入口", "position": [960,800], "is_default": True}],
                    "interactable_points": [
                        {
                            "id": "hidden_body",
                            "name": "角落的帆布",
                            "type": "object",
                            "position": [200,600],
                            "icon": "⚰️",
                            "description": "角落里有一块覆盖着什么的帆布，形状令人不安。",
                            "actions": ["examine", "lift"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "你掀开覆盖的帆布，一具干枯的尸体出现在你面前。从衣着判断，这正是失踪三年的布莱克伍德勋爵！他的面部扭曲，似乎死前经历了极大的痛苦。这不是自然死亡——这是谋杀！",
                                "required_flags": [],
                                "revealed_flags": ["basement_body_found"],
                            },
                        },
                        {
                            "id": "smuggling_ledger",
                            "name": "旧账本",
                            "type": "item",
                            "position": [600,300],
                            "icon": "📒",
                            "description": "一本厚厚的旧账本，放在一个隐蔽的架子上。",
                            "actions": ["examine", "read"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "账本记录着数十年来通过庄园地下通道走私的货物和利润——奢侈品、军火、违禁品。每一页都有威廉的签名和详细记录。这就是威廉的杀人动机——勋爵发现了他的走私活动！",
                                "required_flags": [],
                                "revealed_flags": ["butler_motive_revealed"],
                            },
                        },
                        {
                            "id": "contraband_crates",
                            "name": "密封木箱",
                            "type": "object",
                            "position": [1100,300],
                            "icon": "📦",
                            "description": "几个密封的木箱，上面印着外国文字。",
                            "actions": ["examine", "open"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "木箱中装满了来自欧洲大陆的违禁品——战时走私的奢侈品和军火。这些货物的价值足以让任何人铤而走险。",
                                "required_flags": [],
                                "revealed_flags": ["contraband_found"],
                            },
                        },
                        {
                            "id": "secret_tunnel",
                            "name": "暗道",
                            "type": "exit",
                            "position": [100,450],
                            "icon": "🚪",
                            "description": "一条通往外界的秘密通道，用于走私货物。",
                            "actions": ["examine", "enter"],
                            "conditions": {},
                            "target_scene": "garden",
                            "target_position": [300,800],
                            "investigation": {
                                "clue_text": "这条暗道通向花园的隐蔽处，是走私货物的秘密通道。威廉就是通过这里将违禁品运进运出庄园的。",
                                "required_flags": [],
                                "revealed_flags": ["tunnel_discovered"],
                            },
                        },
                        {
                            "id": "basement_exit_north",
                            "name": "返回花园",
                            "type": "exit",
                            "position": [960,100],
                            "icon": "🚪",
                            "description": "返回花园。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "garden",
                            "target_position": [960,200],
                        },
                    ],
                },
                "connected_scenes": {"north": "garden"},
                "entry_conditions": {"type": "flag", "flag": "basement_key_found", "value": True, "deny_message": "地下室的门被一把生锈的锁锁住了，你需要找到钥匙才能进入。"},
                "on_enter": {"narration_override": "你用那把生锈的钥匙打开了地下室的门。一股腐朽的气味扑面而来，黑暗中似乎有什么东西在等待着你...", "set_flags": ["basement_entered"]},
                "sort_order": 6,
            },
            # Scene 7: Study (NEW)
            {
                "scene_key": "study",
                "name": "庄园书房",
                "description": "勋爵的私人书房，厚重的橡木门半掩着。书桌上散落着未完成的信件，壁炉中还有未燃尽的纸灰。墙上挂着一幅巨大的庄园地图，似乎标注着什么重要的信息。",
                "background_image": scene_bg_urls.get("study", ""),
                "map_data": {
                    "width": 1200,
                    "height": 800,
                    "grid_size": 32,
                    "tiles": [[1,1,1,1,1,1,1],[1,0,0,0,0,0,1],[1,0,2,0,3,0,1],[1,0,0,0,0,0,1],[1,1,1,1,1,1,1]],
                    "walkable_areas": [{"id": "study_main", "name": "书房主区域", "polygon": [[100,100],[1100,100],[1100,700],[100,700]]}],
                    "obstacles": [
                        {"id": "desk", "name": "书桌", "polygon": [[500,300],[700,300],[700,500],[500,500]], "is_solid": True},
                        {"id": "bookshelf", "name": "书架", "polygon": [[100,100],[300,100],[300,600],[100,600]], "is_solid": True},
                    ],
                    "spawn_points": [{"id": "study_entrance", "name": "书房入口", "position": [960,200], "is_default": True}],
                    "interactable_points": [
                        {
                            "id": "locked_drawer",
                            "name": "上锁的抽屉",
                            "type": "object",
                            "position": [600,400],
                            "icon": "🔒",
                            "description": "书桌的一个抽屉被锁住了，需要密码才能打开。",
                            "actions": ["examine", "unlock"],
                            "conditions": {"unlock": [{"type": "flag", "flag": "diary_read", "value": True}]},
                            "investigation": {
                                "clue_text": "你想起日记中提到的日期——勋爵失踪的那天是10月15日。输入'1015'，抽屉弹开了。里面有一张伦敦律师的名片，背面写着'已安排会面，周二讨论遗产事宜'。勋爵正在修改遗嘱！",
                                "required_flags": ["diary_read"],
                                "revealed_flags": ["solicitor_contact"],
                            },
                        },
                        {
                            "id": "will_document",
                            "name": "遗嘱草稿",
                            "type": "item",
                            "position": [550,350],
                            "icon": "📜",
                            "description": "一份未完成的遗嘱修改书，上面有很多修改痕迹。",
                            "actions": ["examine", "read"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "遗嘱显示勋爵打算将庄园捐赠给国家信托，而不是留给任何人。如果这份遗嘱生效，所有依赖庄园的人——包括威廉——都将失去一切。这是威廉的另一个杀人动机！",
                                "required_flags": [],
                                "revealed_flags": ["will_read"],
                            },
                        },
                        {
                            "id": "fireplace_ashes",
                            "name": "壁炉灰烬",
                            "type": "object",
                            "position": [900,600],
                            "icon": "🔥",
                            "description": "壁炉中还有未燃尽的纸灰，似乎有人试图销毁什么文件。",
                            "actions": ["examine", "search"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "你在灰烬中找到一片未烧尽的纸角，上面写着'...威廉必须离开...不能再信任...他知道的太多了...'。勋爵已经决定解雇威廉！",
                                "required_flags": [],
                                "revealed_flags": ["burned_letter_clue"],
                            },
                        },
                        {
                            "id": "manor_map",
                            "name": "庄园地图",
                            "type": "object",
                            "position": [200,400],
                            "icon": "🗺️",
                            "description": "一幅巨大的庄园地图，上面有一些红笔标注。",
                            "actions": ["examine"],
                            "conditions": {},
                            "investigation": {
                                "clue_text": "地图上用红笔标注了一条从地下室通向花园密道的路线，旁边写着'紧急撤离路线'。这是走私者使用的逃生通道！",
                                "required_flags": [],
                                "revealed_flags": ["map_markings"],
                            },
                        },
                        {
                            "id": "study_exit_north",
                            "name": "返回大厅",
                            "type": "exit",
                            "position": [960,100],
                            "icon": "🚪",
                            "description": "返回庄园大厅。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "lobby",
                            "target_position": [960,900],
                        },
                        {
                            "id": "study_exit_west",
                            "name": "通往图书馆",
                            "type": "exit",
                            "position": [100,450],
                            "icon": "🚪",
                            "description": "一扇连接图书馆的小门。",
                            "actions": ["enter"],
                            "conditions": {},
                            "target_scene": "library",
                            "target_position": [1500,450],
                        },
                    ],
                },
                "connected_scenes": {"north": "lobby", "west": "library"},
                "sort_order": 7,
            },
        ]
        for sd in scenes_data:
            scene = Scene(script_id=script.id, **sd)
            session.add(scene)

        # Create characters (5 characters)
        characters_data = [
            # Character 1: Butler William (HIDDEN BOSS)
            {
                "character_key": "butler",
                "name": "管家威廉",
                "display_name": "威廉",
                "role_type": "npc",
                "avatar_url": char_avatar_urls.get("butler", ""),
                "appearance": "身材高大，穿着整洁的黑色燕尾服，银白色的头发梳得一丝不苟。眼神深邃，似乎隐藏着无数秘密。他的双手总是微微颤抖，仿佛在极力控制着什么。",
                "personality": {"traits": ["沉稳", "神秘", "控制欲强"], "mbti": "ISTJ"},
                "background": "在庄园服务了40年，见证了庄园的兴衰。表面上忠诚可靠，实际上掌控着庄园地下走私网络。布莱克伍德勋爵发现真相后，他不得不采取'措施'来保护自己的秘密。",
                "secrets": {"secret": "谋杀布莱克伍德勋爵并掩盖走私罪行", "trust_threshold": 90, "is_hidden_boss": True},
                "dialogue_style": "说话简洁有力，常用敬语，偶尔会意味深长地停顿。当话题涉及地下室或勋爵失踪时，会不自觉地紧张，试图转移话题。",
                "ai_prompt": "你是隐藏的真凶。当玩家接近真相时，试图转移怀疑到其他人身上（如玛格丽特夫人或医生）。如果被直接质问，先否认，只有在铁证如山时才可能崩溃。你的目标是保护自己的秘密，不惜一切代价。",
                "sort_order": 1,
            },
            # Character 2: Lady Margaret (Red Herring)
            {
                "character_key": "lady_margaret",
                "name": "玛格丽特夫人",
                "display_name": "玛格丽特",
                "role_type": "npc",
                "avatar_url": char_avatar_urls.get("lady_margaret", ""),
                "appearance": "优雅的中年女性，穿着华丽的黑色晚礼服，颈间戴着璀璨的钻石项链。她的眼神中带着深深的忧郁，似乎背负着沉重的秘密。",
                "personality": {"traits": ["优雅", "忧郁", "聪慧"], "mbti": "INFJ"},
                "background": "庄园主人的遗孀，据说她的丈夫在三年前的一个雨夜神秘失踪。她很少离开庄园，整日沉浸在回忆中。她知道丈夫打算离开她，但不知道他已经死了。",
                "secrets": {"secret": "知道丈夫打算离开她，但不知道他已死", "trust_threshold": 60},
                "dialogue_style": "说话轻柔，喜欢引用诗句，有时会突然陷入沉思。当提到丈夫时，她的眼神会变得复杂——既有怨恨，也有思念。",
                "sort_order": 2,
            },
            # Character 3: Doctor Holmes (Red Herring)
            {
                "character_key": "doctor_holmes",
                "name": "福尔摩斯医生",
                "display_name": "医生",
                "role_type": "npc",
                "avatar_url": char_avatar_urls.get("doctor_holmes", ""),
                "appearance": "戴着金丝眼镜的中年男子，总是随身携带一个黑色医疗箱。他的目光锐利，似乎在观察着每一个人。手指修长，动作精准。",
                "personality": {"traits": ["理性", "观察力强", "有些神经质"], "mbti": "INTP"},
                "background": "来自伦敦的'医生'，受邀来庄园为玛格丽特夫人看病。实际上他是受雇于勋爵姐姐的私家侦探，来调查勋爵失踪的真相。他的枪和假证件都是为了调查工作。",
                "secrets": {"secret": "受雇调查勋爵失踪案的私家侦探，非真正医生", "trust_threshold": 70},
                "dialogue_style": "喜欢用专业术语，说话快速，经常打断别人。他对案件的细节特别敏感，会追问一些看似无关的问题。",
                "sort_order": 3,
            },
            # Character 4: Cook Martha (Key Witness)
            {
                "character_key": "cook_martha",
                "name": "厨师玛莎",
                "display_name": "玛莎",
                "role_type": "npc",
                "avatar_url": char_avatar_urls.get("cook_martha", ""),
                "appearance": "身材圆润的中年妇女，围着沾满油渍的围裙，脸上总是挂着和善的微笑。但她的眼神中偶尔闪过一丝忧虑，似乎知道一些不该知道的事情。",
                "personality": {"traits": ["健谈", "善良", "八卦"], "mbti": "ESFJ"},
                "background": "在庄园工作了20年的厨师，对庄园里发生的一切了如指掌。她喜欢在厨房里八卦，但有些事情她选择沉默——因为她害怕。",
                "secrets": {"secret": "当晚看到威廉深夜出入地下室", "trust_threshold": 50},
                "dialogue_style": "说话热情，喜欢用食物比喻，经常欲言又止。需要鼓励和信任才会说出关键信息。她害怕威廉，但又同情玛格丽特夫人。",
                "sort_order": 4,
            },
            # Character 5: Young Master Edward (Red Herring)
            {
                "character_key": "young_master",
                "name": "少爷爱德华",
                "display_name": "爱德华",
                "role_type": "npc",
                "avatar_url": char_avatar_urls.get("young_master", ""),
                "appearance": "年轻英俊但面容憔悴的男子，穿着略显破旧的西装，手指上有赌场留下的墨迹。他的眼神中带着焦虑和愧疚。",
                "personality": {"traits": ["急躁", "狡猾", "脆弱"], "mbti": "ESTP"},
                "background": "布莱克伍德勋爵的独子，因赌博与父亲决裂后离家出走。三年后突然回到庄园，声称是为了'悼念父亲'，但所有人都知道他急需钱来还赌债。然而，勋爵失踪的那晚他确实在伦敦。",
                "secrets": {"secret": "欠下巨额赌债，急需遗产，但当晚不在庄园", "trust_threshold": 40},
                "dialogue_style": "说话急促，经常转移话题，对金钱相关的话题特别敏感。偶尔流露出对父亲的愧疚，但更多的是对遗产的渴望。",
                "sort_order": 5,
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
