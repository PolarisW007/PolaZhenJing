from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
FIG = BASE / "figures" / "author_frequency"
OUT = BASE / "output"
INPUT = FIG / "fig3_high_frequency_authors_top25_data.csv"
OUTPUT = FIG / "fig3_high_frequency_authors_top25_data_augmented.csv"
OUTPUT_XLSX = FIG / "fig3_high_frequency_authors_top25_data_augmented.xlsx"
OUTPUT_USER_UPDATES = FIG / "fig3_user_confirmed_author_updates.csv"
FIG.mkdir(parents=True, exist_ok=True)


# 口径：
# 1. 中文名只写公开资料能对应到英文名的人；不确定者不硬猜。
# 2. 背景信息优先采用个人主页、学校/实验室页、OpenReview 等可核来源。
# 3. 对媒体二手信息保留 source_type，后续写稿前仍建议二次核对。
ENRICHMENT = {
    "Chong Ruan": {
        "chinese_name": "阮翀",
        "chinese_name_status": "已核验",
        "background_summary": "公开报道称其2018年毕业于北京大学计算语言研究所，2023年加入DeepSeek；DeepSeek-VL论文/仓库显示其为多模态相关作者之一，媒体称其已加盟元戎启行任首席科学家。",
        "background_level": "B：媒体+论文/仓库",
        "source_urls": "https://www.donews.com/news/detail/1/6384208.html; https://github.com/deepseek-ai/DeepSeek-VL; https://finance.sina.com.cn/stock/t/2026-05-07/doc-inhwzrtk7860301.shtml",
        "source_note": "中文名和履历主要来自DoNews/腾讯汽车口径；离职流向来自雷科技转载稿，需以本人或公司确认优先。",
    },
    "Zhenda Xie": {
        "chinese_name": "解振达",
        "chinese_name_status": "已核验",
        "background_summary": "DeepSeek AI研究员；个人主页称其2023年获清华大学博士，导师为郭百宁，本科毕业于中国科学技术大学；2018-2023年在微软亚洲研究院实习，研究方向包括基础模型预训练与Scaling。",
        "background_level": "A：个人主页",
        "source_urls": "https://zdaxie.github.io/; https://asiatimes.com/2025/02/where-deepseek-qwens-ai-engineers-really-come-from/",
        "source_note": "个人主页与媒体报道相互印证清华博士、MSRA经历。",
    },
    "Damai Dai": {
        "chinese_name": "代达劢",
        "chinese_name_status": "已核验",
        "background_summary": "OpenReview显示其为DeepSeek研究员，2019-2024年北京大学计算机博士，2015-2019年北京大学本科，导师为穗志方；研究方向标注为大语言模型和MoE模型。",
        "background_level": "A/B：OpenReview+媒体/榜单",
        "source_urls": "https://openreview.net/profile?id=~Damai_Dai1; https://www.cnpp.cn/focus/3516653.html; https://www.scmp.com/tech/big-tech/article/3294357/chinas-ai-disrupter-deepseek-bets-low-key-team-young-geniuses-beat-us-giants",
        "source_note": "中文名采用CNPP/公开报道写法；OpenReview用于学历和研究方向。",
    },
    "Wenfeng Liang": {
        "chinese_name": "梁文锋",
        "chinese_name_status": "已核验",
        "background_summary": "DeepSeek创始人兼CEO；公开报道称其毕业于浙江大学，曾创办/参与幻方量化，DeepSeek由幻方量化孵化。",
        "background_level": "B：媒体/百科",
        "source_urls": "https://www.scmp.com/tech/big-tech/article/3294357/chinas-ai-disrupter-deepseek-bets-low-key-team-young-geniuses-beat-us-giants; https://en.wikipedia.org/wiki/DeepSeek",
        "source_note": "创始人身份公开资料较多；学历和幻方背景采用媒体/百科口径。",
    },
    "Huazuo Gao": {
        "chinese_name": "高华佐",
        "chinese_name_status": "已核验",
        "background_summary": "OpenReview显示其为DeepSeek研究员，2013-2018年北京大学本科；SCMP/Firstpost等报道称其毕业于北大物理系，并被DeepSeek方面点名为MLA架构关键创新人员之一。",
        "background_level": "A/B：OpenReview+媒体",
        "source_urls": "https://openreview.net/profile?id=~Huazuo_Gao1; https://www.scmp.com/tech/big-tech/article/3294357/chinas-ai-disrupter-deepseek-bets-low-key-team-young-geniuses-beat-us-giants; https://www.firstpost.com/explainers/china-deepseek-ai-full-team-liang-wenfeng-luo-fuli-13857438.html",
        "source_note": "中文名来自CNPP/Mapping Studio等二手资料，背景用OpenReview和媒体报道交叉。",
    },
    "Qihao Zhu": {
        "chinese_name": "朱启豪",
        "chinese_name_status": "待复核",
        "background_summary": "个人主页称其近期完成北京大学计算机博士，导师熊英飞，研究方向为程序生成、程序理解、预训练大模型和NLP；北大页面称其博士论文获CCF TCSE优秀博士论文，论文工作应用于DeepSeek-Coder-V1。",
        "background_level": "A：个人主页+学校页面",
        "source_urls": "https://pkuzqh.github.io/; https://pl.cs.pku.edu.cn/en/info/1082/1942.htm; https://www.cnpp.cn/focus/3516653.html",
        "source_note": "英文名与履历可核；中文名公开资料有“朱启豪/朱琪豪”两种写法，表中先采用个人域名/检索更常见的朱启豪，建议报道前向本人或DeepSeek确认。",
    },
    "Zhihong Shao": {
        "chinese_name": "邵智宏",
        "chinese_name_status": "已核验",
        "background_summary": "个人主页显示其为DeepSeek研究科学家，研究自我改进系统、工具使用和推理；获清华大学计算机博士，导师黄民烈；曾入选MIT Technology Review 35 Innovators Under 35。",
        "background_level": "A：个人主页",
        "source_urls": "https://zhihongshao.github.io/; https://asiatimes.com/2025/02/where-deepseek-qwens-ai-engineers-really-come-from/",
        "source_note": "个人主页信息完整；Asia Times补充其清华/MSRA论文关系。",
    },
    "Chengqi Deng": {
        "chinese_name": "邓乘奇",
        "chinese_name_status": "媒体来源",
        "background_summary": "DeepSeekMoE、DeepSeek-VL、V3/R1等多篇论文作者；DoNews报道提到其为与梁文锋共同署名论文较多的研究人员之一。公开学历背景暂未找到可靠一手来源。",
        "background_level": "C：论文署名+媒体",
        "source_urls": "https://www.donews.com/news/detail/1/6384208.html; https://ir.pku.edu.cn/handle/20.500.11897/739769; https://huggingface.co/papers/2505.09343",
        "source_note": "中文名来自DoNews转载口径；学历/经历暂缺一手公开资料。",
    },
    "Liyue Zhang": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "公开论文显示其为DeepSeek-V3硬件/架构反思论文《Insights into DeepSeek-V3》的作者之一；该论文注明Liyue Zhang与Yuqing Wang为通信作者之一。其他个人背景暂未找到可靠公开资料。",
        "background_level": "D：论文署名",
        "source_urls": "https://huggingface.co/papers/2505.09343; https://www.52nlp.cn/wp-content/uploads/2025/05/Insights-into-DeepSeek-V3%E8%8B%B1%E4%B8%AD%E5%AF%B9%E7%85%A7%E7%89%88.pdf",
        "source_note": "不硬译中文名。",
    },
    "Shirong Ma": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "OpenReview显示其为DeepSeek AI研究员，清华大学本科和硕士背景；论文记录涉及DeepSeek-R1、DeepSeekMath及Inference-Time Scaling for Generalist Reward Modeling等。",
        "background_level": "B：OpenReview",
        "source_urls": "https://openreview.net/profile?id=~Shirong_Ma1; https://huggingface.co/papers/2501.12948",
        "source_note": "中文名暂不猜测。",
    },
    "Daya Guo": {
        "chinese_name": "郭达雅",
        "chinese_name_status": "已核验",
        "background_summary": "个人主页显示其为DeepSeek研究员，中山大学计算机博士，MSRA联合培养；研究方向为NLP、代码智能、大语言模型。媒体报道称其已加入字节跳动Seed团队，任Agent方向负责人之一。",
        "background_level": "A/B：个人主页+媒体",
        "source_urls": "https://guoday.github.io/index.html; https://asiatimes.com/2025/02/where-deepseek-qwens-ai-engineers-really-come-from/; https://finance.sina.com.cn/stock/t/2026-05-07/doc-inhwzrtk7860301.shtml",
        "source_note": "流向为媒体报道，报道前建议再核。",
    },
    "Xingkai Yu": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "GitHub个人页显示其账号关联DeepSeek-AI与南京大学；仓库包括DeepSeek-V3、DeepSeek-R1、nano-vllm等。公开学历细节暂未找到可靠资料。",
        "background_level": "B/C：GitHub+论文署名",
        "source_urls": "https://github.com/GeeeekExplorer; https://ir.pku.edu.cn/handle/20.500.11897/739769",
        "source_note": "中文名暂不猜测。",
    },
    "Bingxuan Wang": {
        "chinese_name": "王炳宣",
        "chinese_name_status": "已核验",
        "background_summary": "北京大学Camera Intelligence团队页面显示其2024年获北大硕士，下一站为DeepSeek研究工程师；媒体报道称其为DeepSeek第一代大语言模型核心作者之一，后加入腾讯混元团队。",
        "background_level": "A/B：学校团队页+媒体",
        "source_urls": "https://ci.idm.pku.edu.cn/team; https://finance.sina.com.cn/stock/t/2026-05-07/doc-inhwzrtk7860301.shtml",
        "source_note": "流向为媒体报道。",
    },
    "Chenggang Zhao": {
        "chinese_name": "赵成刚",
        "chinese_name_status": "已核验",
        "background_summary": "清华大学高明宇老师学生页显示其2024年硕士毕业，下一站DeepSeek；公开资料称其在DeepSeek担任训练/推理基础架构工程相关角色，论文涉及MoE、V3硬件架构反思等。",
        "background_level": "A/B：学校页面+公开资料",
        "source_urls": "https://people.iiis.tsinghua.edu.cn/~gaomy/students.html; https://www.cnpp.cn/focus/3516653.html; https://huggingface.co/papers/2505.09343",
        "source_note": "中文名和学校去向可核；岗位描述来自二手公开资料。",
    },
    "Dejian Yang": {
        "chinese_name": "杨德健",
        "chinese_name_status": "待复核",
        "background_summary": "OpenReview显示其为DeepSeek AI代码方向研究员，2012-2019年在北京航空航天大学完成本科和硕士，2019-2023年在微软亚洲研究院任研究员；参与DeepSeek-Coder、R1等项目。",
        "background_level": "B：OpenReview",
        "source_urls": "https://openreview.net/profile?id=~Dejian_Yang1; https://huggingface.co/papers/2501.12948",
        "source_note": "中文名来自姓名音译/日文索引转写，未找到本人中文页，建议复核。",
    },
    "Jiashi Li": {
        "chinese_name": "李嘉实",
        "chinese_name_status": "媒体来源",
        "background_summary": "DeepSeekMoE、R1、Insights into DeepSeek-V3等论文作者；DoNews报道称其为与梁文锋共同署名论文较多的研究人员之一。公开学历背景暂未找到可靠一手来源。",
        "background_level": "C：论文署名+媒体",
        "source_urls": "https://www.donews.com/news/detail/1/6384208.html; https://ir.pku.edu.cn/handle/20.500.11897/739769; https://huggingface.co/papers/2505.09343",
        "source_note": "中文名来自DoNews口径。",
    },
    "Junxiao Song": {
        "chinese_name": "宋俊潇",
        "chinese_name_status": "已核验",
        "background_summary": "香港科技大学工学院页面列其为HKUST杰出校友、DeepSeek AI首席研究员；其为DeepSeekMath、DeepSeek-R1等论文作者。",
        "background_level": "A：学校页面",
        "source_urls": "https://sengexe.hkust.edu.hk/zh-hans/launchpad-global-leaders; https://huggingface.co/papers/2501.12948",
        "source_note": "学校页面有中文名和身份描述。",
    },
    "Kai Dong": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "DeepSeek-Coder、DeepSeek-VL、DeepSeek LLM等论文作者；公开个人背景暂未找到可靠来源。",
        "background_level": "D：论文署名",
        "source_urls": "https://github.com/deepseek-ai/DeepSeek-VL; https://huggingface.co/papers/2401.02954",
        "source_note": "不硬译中文名。",
    },
    "Wangding Zeng": {
        "chinese_name": "曾旺丁",
        "chinese_name_status": "媒体来源",
        "background_summary": "Hugging Face个人页显示其署名DeepSeekMoE、DeepSeek-Coder-V2和mHC等论文；SCMP/Firstpost报道称其在2021年开始于北京邮电大学人工智能学院攻读硕士，并被DeepSeek点名为MLA架构关键创新人员之一。",
        "background_level": "B/C：HF主页+媒体",
        "source_urls": "https://huggingface.co/zwd973-deepseek; https://www.scmp.com/tech/big-tech/article/3294357/chinas-ai-disrupter-deepseek-bets-low-key-team-young-geniuses-beat-us-giants; https://www.firstpost.com/explainers/china-deepseek-ai-full-team-liang-wenfeng-luo-fuli-13857438.html",
        "source_note": "中文名来自CNPP/媒体口径，另有资料写作Zeng Wangding。",
    },
    "Yaofeng Sun": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "DeepSeek-VL论文作者之一，并出现在DeepSeek LLM/R1等多篇论文中；公开个人教育和履历暂未找到可靠资料。",
        "background_level": "D：论文署名",
        "source_urls": "https://github.com/deepseek-ai/DeepSeek-VL; https://huggingface.co/papers/2501.12948",
        "source_note": "不硬译中文名。",
    },
    "Wen Liu": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "OpenReview显示其为DeepSeek AI研究员，2016-2021年上海科技大学博士，2012-2016年西北工业大学本科；曾在腾讯PCG任研究员，研究方向包括大多模态模型、神经3D表示与生成、图像/视频生成等。",
        "background_level": "B：OpenReview",
        "source_urls": "https://openreview.net/profile?id=~Wen_Liu2; https://github.com/deepseek-ai/DeepSeek-VL",
        "source_note": "中文名暂不猜测。",
    },
    "Runxin Xu": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "OpenReview显示其为DeepSeek研究员，2020-2023年北京大学硕士；标注研究方向包括多语言和信息抽取。参与DeepSeekMath、R1及Generalist Reward Modeling等论文。",
        "background_level": "B：OpenReview",
        "source_urls": "https://openreview.net/profile?id=~Runxin_Xu2; https://huggingface.co/papers/2501.12948",
        "source_note": "不硬译中文名。",
    },
    "Deli Chen": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "OpenReview显示其为DeepSeek AI研究员，2018-2021年北京大学硕士，2021-2023年在腾讯微信AI任研究员；论文涉及联邦学习、文本水印、上下文学习等，也参与DeepSeek LLM/MoE/R1。",
        "background_level": "B：OpenReview",
        "source_urls": "https://openreview.net/profile?id=~Deli_Chen1; https://huggingface.co/papers/2501.12948",
        "source_note": "不硬译中文名。",
    },
    "Peiyi Wang": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "公开资料称其为北京大学博士背景、DeepSeekMath核心作者之一；论文署名显示其参与Math-Shepherd、DeepSeekMath、R1和Generalist Reward Modeling等数学/推理相关工作。",
        "background_level": "C：公开资料+论文署名",
        "source_urls": "https://www.cnpp.cn/focus/3516653.html; https://hub.baai.ac.cn/paper/0fe070a4-5415-41ec-ae4d-7ef849658d67; https://huggingface.co/papers/2501.12948",
        "source_note": "中文名暂不猜测；北大博士背景来自二手公开资料。",
    },
    "Wenjun Gao": {
        "chinese_name": "",
        "chinese_name_status": "未找到可靠公开中文名",
        "background_summary": "DeepSeek LLM、DeepSeekMath/Prover等论文作者；公开个人教育和履历暂未找到可靠资料。",
        "background_level": "D：论文署名",
        "source_urls": "https://huggingface.co/papers/2401.02954; https://huggingface.co/papers/2501.12948",
        "source_note": "不硬译中文名。",
    },
}


USER_CONFIRMED_UPDATES = {
    "Yukun Li": {"chinese_name": "李宇琨"},
    "Yu Wu": {"chinese_name": "吴俣"},
    "Chengqi Deng": {"chinese_name": "邓乘奇", "school": "浙江大学"},
    "Liyue Zhang": {"chinese_name": "张力越", "school": "中山大学"},
    "Xingkai Yu": {"chinese_name": "俞星凯", "school": "南京大学"},
    "Jiashi Li": {"school": "北京大学"},
    "Yaofeng Sun": {"chinese_name": "孙耀峰", "school": "北京大学"},
    "Wen Liu": {"chinese_name": "刘闻"},
    "Runxin Xu": {"chinese_name": "许润昕"},
    "Deli Chen": {"chinese_name": "陈德里"},
    "Qihao Zhu": {"chinese_name": "朱琪豪"},
    "Wangding Zeng": {"chinese_name": "曾旺丁"},
    "Wenjun Gao": {"school": "上海交通大学"},
}


def main() -> None:
    df = pd.read_csv(INPUT, encoding="utf-8-sig")
    if "rank" not in df.columns:
        df.insert(0, "rank", range(1, len(df) + 1))

    for col in [
        "chinese_name",
        "chinese_name_status",
        "background_summary",
        "background_level",
        "source_urls",
        "source_note",
        "confirmed_school",
        "user_update_note",
    ]:
        df[col] = ""

    for idx, row in df.iterrows():
        info = ENRICHMENT.get(row["author"], {})
        for key, value in info.items():
            df.at[idx, key] = value
        update = USER_CONFIRMED_UPDATES.get(row["author"], {})
        if update.get("chinese_name"):
            df.at[idx, "chinese_name"] = update["chinese_name"]
            df.at[idx, "chinese_name_status"] = "用户确认"
        if update.get("school"):
            df.at[idx, "confirmed_school"] = update["school"]
        if update:
            details = []
            if update.get("chinese_name"):
                details.append(f"中文名：{update['chinese_name']}")
            if update.get("school"):
                details.append(f"院校：{update['school']}")
            note = "用户于2026-05-09手动核验补充：" + "；".join(details)
            df.at[idx, "user_update_note"] = note
            current_note = str(df.at[idx, "source_note"]).strip()
            df.at[idx, "source_note"] = f"{current_note}；{note}" if current_note else note
            if update.get("school"):
                current_summary = str(df.at[idx, "background_summary"]).strip()
                school_sentence = f"用户手动核验补充其院校背景为{update['school']}。"
                df.at[idx, "background_summary"] = (
                    f"{current_summary} {school_sentence}".strip() if current_summary else school_sentence
                )

    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    if (OUT / "chart6_high_frequency_authors.csv").exists():
        high = pd.read_csv(OUT / "chart6_high_frequency_authors.csv", encoding="utf-8-sig")
        high.insert(0, "current_rank", range(1, len(high) + 1))
        update_rows = []
        for author, update in USER_CONFIRMED_UPDATES.items():
            row = high.loc[high["author"].eq(author)].head(1)
            item = {
                "author": author,
                "chinese_name": update.get("chinese_name", ""),
                "confirmed_school": update.get("school", ""),
                "user_update_note": "用户于2026-05-09手动核验补充",
            }
            if not row.empty:
                item.update(
                    {
                        "current_rank": int(row.iloc[0]["current_rank"]),
                        "paper_count": int(row.iloc[0]["paper_count"]),
                        "topic_count": int(row.iloc[0]["topic_count"]),
                        "in_current_top25": int(row.iloc[0]["current_rank"]) <= 25,
                    }
                )
            update_rows.append(item)
        pd.DataFrame(update_rows).to_csv(OUTPUT_USER_UPDATES, index=False, encoding="utf-8-sig")
    try:
        df.to_excel(OUTPUT_XLSX, index=False)
    except Exception as exc:
        print(f"Skipped xlsx export: {exc}")
    print(OUTPUT)


if __name__ == "__main__":
    main()

