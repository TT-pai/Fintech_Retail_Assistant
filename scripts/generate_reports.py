"""
生成扩充研报数据
时间范围：2025年4月 - 2026年4月
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# 券商列表
BROKERS = [
    "中信证券", "华泰证券", "国泰君安", "招商证券", "海通证券",
    "东方证券", "中金公司", "广发证券", "申万宏源", "兴业证券",
    "开源证券", "天风证券", "东吴证券", "长江证券", "民生证券",
    "浙商证券", "国盛证券", "华西证券", "财通证券", "中银证券"
]

# 行业和标的配置
INDUSTRIES = {
    "白酒": {
        "stocks": [
            ("600519", "贵州茅台"),
            ("000858", "五粮液"),
            ("000568", "泸州老窖"),
            ("002304", "洋河股份"),
            ("000799", "酒鬼酒"),
            ("603589", "口子窖"),
            ("600809", "山西汾酒"),
            ("603369", "今世缘"),
        ],
        "analysts": ["食品饮料研究团队", "白酒行业分析师", "消费研究团队"],
        "keywords": ["业绩稳健", "品牌升级", "渠道改革", "高端化", "消费升级"]
    },
    "新能源": {
        "stocks": [
            ("300750", "宁德时代"),
            ("002594", "比亚迪"),
            ("600460", "士兰微"),
            ("002129", "中环股份"),
            ("300014", "亿纬锂能"),
            ("002074", "国轩高科"),
            ("600089", "特变电工"),
            ("603501", "威尔泰"),
        ],
        "analysts": ["新能源研究团队", "电新行业分析师", "碳中和研究组"],
        "keywords": ["技术突破", "产能扩张", "市占率提升", "成本下降", "出海加速"]
    },
    "医药": {
        "stocks": [
            ("300760", "迈瑞医疗"),
            ("688180", "君实生物"),
            ("300122", "智飞生物"),
            ("002007", "华兰生物"),
            ("300347", "泰格医药"),
            ("603259", "药明康德"),
            ("300015", "爱尔眼科"),
            ("002475", "立讯精密"),
        ],
        "analysts": ["医药研究团队", "生物医药分析师", "医疗健康组"],
        "keywords": ["创新药突破", "器械国产化", "CXO景气度", "政策利好", "研发进展"]
    },
    "半导体": {
        "stocks": [
            ("688981", "中芯国际"),
            ("002371", "北方华创"),
            ("300661", "圣邦股份"),
            ("688012", "中微公司"),
            ("603501", "韦尔股份"),
            ("002049", "紫光国微"),
            ("300454", "深信服"),
            ("688256", "寒武纪"),
        ],
        "analysts": ["半导体研究团队", "电子行业分析师", "硬科技研究组"],
        "keywords": ["国产替代", "产能释放", "技术突破", "订单饱满", "自主可控"]
    },
    "人工智能": {
        "stocks": [
            ("002230", "科大讯飞"),
            ("300033", "同花顺"),
            ("688787", "海天瑞声"),
            ("300496", "中科创达"),
            ("002405", "四维图新"),
            ("300144", "宋城演艺"),
            ("688111", "金山办公"),
            ("002410", "广联达"),
        ],
        "analysts": ["AI研究团队", "科技行业分析师", "数字经济研究组"],
        "keywords": ["AI应用落地", "大模型进展", "算力需求", "商业化加速", "技术迭代"]
    },
    "银行金融": {
        "stocks": [
            ("601398", "工商银行"),
            ("601288", "农业银行"),
            ("600036", "招商银行"),
            ("601166", "兴业银行"),
            ("000001", "平安银行"),
            ("601318", "中国平安"),
            ("601939", "建设银行"),
            ("601988", "中国银行"),
        ],
        "analysts": ["银行研究团队", "金融行业分析师", "宏观策略组"],
        "keywords": ["息差改善", "资产质量", "财富管理", "数字化转型", "估值修复"]
    },
    "消费电子": {
        "stocks": [
            ("002475", "立讯精密"),
            ("000725", "京东方A"),
            ("002241", "歌尔股份"),
            ("600584", "长电科技"),
            ("603160", "汇顶科技"),
            ("002600", "领益智造"),
            ("600183", "生益科技"),
            ("002049", "同兴达"),
        ],
        "analysts": ["电子研究团队", "消费电子分析师", "硬件研究组"],
        "keywords": ["新品周期", "订单回暖", "产品升级", "客户拓展", "旺季来临"]
    },
    "汽车": {
        "stocks": [
            ("601127", "小康股份"),
            ("000625", "长安汽车"),
            ("600104", "上汽集团"),
            ("601238", "广汽集团"),
            ("002594", "比亚迪"),
            ("601633", "长城汽车"),
            ("000868", "安凯客车"),
            ("603806", "福耀玻璃"),
        ],
        "analysts": ["汽车研究团队", "新能源汽车分析师", "交运设备组"],
        "keywords": ["销量增长", "电动化转型", "智能化升级", "出海战略", "新品发布"]
    },
    "家电": {
        "stocks": [
            ("000333", "美的集团"),
            ("600690", "海尔智家"),
            ("000651", "格力电器"),
            ("002050", "三花智控"),
            ("603486", "科沃斯"),
            ("002705", "新宝股份"),
            ("000021", "深科技"),
            ("600261", "阳光照明"),
        ],
        "analysts": ["家电研究团队", "消费行业分析师", "可选消费组"],
        "keywords": ["内销回暖", "出口增长", "产品升级", "渠道变革", "估值修复"]
    },
    "食品饮料": {
        "stocks": [
            ("600887", "伊利股份"),
            ("000895", "双汇发展"),
            ("603288", "海天味业"),
            ("000568", "泸州老窖"),
            ("002847", "盐津铺子"),
            ("603517", "绝味食品"),
            ("002840", "安井食品"),
            ("600873", "梅花生物"),
        ],
        "analysts": ["食品饮料研究团队", "必选消费分析师", "大消费研究组"],
        "keywords": ["业绩稳健", "渠道扩张", "产品创新", "成本下降", "消费复苏"]
    }
}

# 评级分布权重
RATINGS = ["买入", "增持", "买入", "增持", "买入", "持有", "增持", "买入"]

def generate_date():
    """生成2025年4月到2026年4月的随机日期"""
    start = datetime(2025, 4, 1)
    end = datetime(2026, 4, 8)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")

def generate_report_id(index):
    """生成研报ID"""
    return f"report_{str(index).zfill(3)}"

def generate_title(industry, stock_name, report_type, date):
    """生成研报标题"""
    templates = {
        "深度": f"{stock_name}深度报告：行业龙头优势显著，成长空间广阔",
        "季报": f"{stock_name}{date[:4]}年Q{((int(date[5:7])-1)//3)+1}财报点评：业绩超预期，盈利能力提升",
        "年报": f"{stock_name}{date[:4]}年报点评：营收净利双增长，经营质量持续改善",
        "事件": f"{stock_name}事件点评：重大利好落地，中长期价值凸显",
        "策略": f"{industry}行业2025年中期策略：景气度上行，龙头配置价值凸显",
        "热点": f"{stock_name}热点追踪：市场关注度提升，基本面支撑强劲",
    }
    return templates.get(report_type, f"{stock_name}研究报告")

def generate_content(industry, stock_name, rating, keywords, report_type):
    """生成研报内容"""
    keyword = random.choice(keywords)
    
    templates = {
        "深度": f"""{stock_name}作为{industry}行业龙头企业，在技术创新、品牌建设、渠道布局等方面具备显著优势。公司近年来持续加大研发投入，产品竞争力不断增强。从财务数据看，营收和净利润保持稳健增长，毛利率和净利率处于行业领先水平。
        
管理层战略清晰，执行力强，在行业竞争加剧的背景下仍能保持稳健增长。公司积极拓展新业务，培育新的增长点，中长期发展前景看好。{keyword}趋势明显，将推动公司业绩持续释放。

基于对公司基本面的深入分析和行业景气度的判断，给予"{rating}"评级。风险提示：宏观经济下行、行业竞争加剧、原材料价格波动。""",

        "季报": f"""{stock_name}本季度业绩表现亮眼，营收同比增长{random.randint(15,35)}%，净利润同比增长{random.randint(20,45)}%。业绩超市场预期，主要得益于：1）主营业务稳健增长，市占率持续提升；2）费用管控有效，盈利能力改善；3）{keyword}效应显现。

从经营数据看，公司产品结构持续优化，高端产品占比提升，毛利率同比改善。渠道建设成效显著，线上线下协同发力。展望全年，公司业绩有望保持快速增长。

给予"{rating}"评级，建议投资者积极关注。风险提示：行业景气度不及预期、竞争加剧。""",

        "年报": f"""{stock_name}年报显示，全年实现营收同比增长{random.randint(10,25)}%，净利润同比增长{random.randint(15,35)}。公司经营质量持续改善，现金流状况良好，资产负债结构健康。

分业务看，各业务板块协同发展，主业保持稳健增长，新业务快速放量。公司在研发创新方面持续投入，技术壁垒不断巩固。{keyword}为公司注入新的增长动能。

展望未来，公司将继续深化战略布局，巩固行业领先地位。给予"{rating}"评级。风险提示：市场需求变化、政策风险。""",

        "事件": f"""公司近期发布重大公告，内容涉及{keyword}，对公司发展具有积极意义。此次事件将有助于公司进一步巩固市场地位，提升核心竞争力。

从长期角度看，公司战略布局清晰，执行力强，此次事件是战略落地的重要一步。预计将对公司业绩产生积极影响，中长期投资价值进一步凸显。

维持"{rating}"评级，建议投资者逢低布局。风险提示：事件推进不及预期、市场环境变化。""",

        "策略": f"""{industry}行业当前处于景气上行周期，从行业数据看，需求端保持稳健增长，供给端结构优化，龙头企业优势凸显。

主要投资逻辑：1）{keyword}趋势明确，行业增长空间广阔；2）龙头企业凭借品牌、渠道、技术优势，市占率持续提升；3）政策支持力度加大，行业发展环境改善。

建议重点关注行业龙头企业，配置价值凸显。风险提示：宏观经济下行、政策变化、行业竞争加剧。""",

        "热点": f"""近期{stock_name}受到市场高度关注，主要催化剂包括：1）{keyword}利好持续释放；2）行业景气度上行；3）公司基本面稳健，业绩确定性强。

从技术面看，股价处于合理估值区间，具备较好的安全边际。从基本面看，公司业绩增长确定性强，中长期投资价值显著。

给予"{rating}"评级，建议投资者积极关注投资机会。风险提示：短期市场波动、行业景气度变化。"""
    }
    
    return templates.get(report_type, templates["深度"])

def generate_target_price(rating, industry):
    """生成目标价"""
    if rating == "卖出":
        return None
    
    # 根据行业特征设定价格区间
    price_ranges = {
        "白酒": (800, 2500),
        "新能源": (100, 400),
        "医药": (50, 300),
        "半导体": (50, 200),
        "人工智能": (30, 150),
        "银行金融": (10, 60),
        "消费电子": (20, 80),
        "汽车": (20, 100),
        "家电": (30, 100),
        "食品饮料": (30, 150),
    }
    
    low, high = price_ranges.get(industry, (50, 200))
    
    if rating == "买入":
        return random.randint(int(low * 1.2), high)
    elif rating == "增持":
        return random.randint(int(low * 1.1), int(high * 0.9))
    else:
        return random.randint(low, int(high * 0.8))

def generate_reports(count=120):
    """生成指定数量的研报"""
    reports = []
    report_id = 1
    
    # 计算每个行业的研报数量
    industry_count = len(INDUSTRIES)
    reports_per_industry = count // industry_count
    extra = count % industry_count
    
    # 报告类型分布
    report_types = ["深度", "季报", "季报", "年报", "事件", "热点", "季报", "深度"]
    
    for i, (industry, config) in enumerate(INDUSTRIES.items()):
        # 分配研报数量
        target_count = reports_per_industry + (1 if i < extra else 0)
        
        for j in range(target_count):
            stock_code, stock_name = random.choice(config["stocks"])
            broker = random.choice(BROKERS)
            analyst = random.choice(config["analysts"])
            report_type = random.choice(report_types)
            rating = random.choice(RATINGS)
            date = generate_date()
            
            # 生成标题
            if report_type == "策略":
                title = f"{industry}行业策略报告：景气度研判与投资建议"
                content = generate_content(industry, stock_name, rating, config["keywords"], report_type)
                stock_code_final = None
                stock_name_final = None
            else:
                title = generate_title(industry, stock_name, report_type, date)
                content = generate_content(industry, stock_name, rating, config["keywords"], report_type)
                stock_code_final = stock_code
                stock_name_final = stock_name
            
            report = {
                "id": generate_report_id(report_id),
                "title": title,
                "content": content,
                "source": broker,
                "author": analyst,
                "date": date,
                "stock_code": stock_code_final,
                "stock_name": stock_name_final,
                "rating": rating if report_type != "策略" else None,
                "target_price": generate_target_price(rating, industry) if report_type != "策略" else None,
                "doc_type": "report"
            }
            
            reports.append(report)
            report_id += 1
    
    # 按日期排序
    reports.sort(key=lambda x: x["date"], reverse=True)
    
    # 重新分配ID
    for i, report in enumerate(reports):
        report["id"] = generate_report_id(i + 1)
    
    return reports

def main():
    """主函数"""
    print("开始生成研报数据...")
    
    # 生成研报
    reports = generate_reports(120)
    
    # 保存文件
    output_path = Path(__file__).parent.parent / "knowledge_base" / "reports.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=4)
    
    print(f"成功生成 {len(reports)} 份研报")
    print(f"文件保存至: {output_path}")
    
    # 统计信息
    print("\n=== 统计信息 ===")
    
    # 按行业统计
    industries_count = {}
    brokers_count = {}
    dates = []
    
    for r in reports:
        # 统计券商
        broker = r["source"]
        brokers_count[broker] = brokers_count.get(broker, 0) + 1
        
        # 统计日期
        dates.append(r["date"])
    
    print(f"时间范围: {min(dates)} ~ {max(dates)}")
    print(f"券商数量: {len(brokers_count)}")
    print(f"研报总数: {len(reports)}")

if __name__ == "__main__":
    main()
