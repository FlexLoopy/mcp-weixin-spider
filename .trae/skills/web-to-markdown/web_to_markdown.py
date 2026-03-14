#!/usr/bin/env python3
"""
Web to Markdown Converter
将网页转换为Markdown格式，保留主要内容结构和格式
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class WebToMarkdownConverter:
    """网页到Markdown转换器"""
    
    def __init__(self, url):
        """初始化转换器"""
        self.url = url
        self.soup = None
        self.title = ""
        self.content = ""
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    def fetch_webpage(self):
        """获取网页内容"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(self.url, headers=headers)
        # 优先尝试utf-8编码
        response.encoding = 'utf-8'
        # 如果utf-8解码失败，尝试其他编码
        try:
            content = response.text
        except UnicodeDecodeError:
            response.encoding = response.apparent_encoding
            content = response.text
        self.soup = BeautifulSoup(content, "html.parser")
    
    def extract_title(self):
        """提取网页标题"""
        if not self.soup:
            self.fetch_webpage()
        
        # 尝试h1标签（优先，因为这通常是文章的实际标题）
        h1_tag = self.soup.find("h1")
        if h1_tag:
            self.title = h1_tag.text.strip()
        else:
            # 尝试title标签
            title_tag = self.soup.find("title")
            if title_tag:
                self.title = title_tag.text.strip()
                # 移除微信公众号标题中的多余后缀
                for suffix in [" - 微信公众号", "_微信公众号"]:
                    if self.title.endswith(suffix):
                        self.title = self.title[:-len(suffix)]
            else:
                self.title = f"网页转换_{self.timestamp}"
    
    def remove_unnecessary_elements(self):
        """移除不必要的元素"""
        if not self.soup:
            return
        
        # 需要移除的元素类型
        selectors_to_remove = [
            "script", "style", "iframe", "nav", "footer", "header",
            "aside", "ad", "advertisement", "#ads", ".ads", ".advertisement",
            ".sidebar", ".nav", ".footer", ".header", ".comment", ".comments",
            ".related", ".share", ".social", ".breadcrumb", ".pagination",
            # 微信公众号特有元素
            ".weixin-share-btn", ".weixin-subscribe", ".subscribe", ".qr-code",
            ".copyright", ".author-info", ".article-meta", ".meta-info",
            ".post-meta", ".article-header", ".article-footer", ".wx_tip",
            ".wx_header", ".wx_footer", ".wx_nav", ".wx_sidebar",
            # 微信公众号引导文字（通过文本内容匹配）
        ]
        
        for selector in selectors_to_remove:
            # 尝试不同的选择器类型
            for element in self.soup.select(selector):
                element.decompose()
        
        # 移除微信公众号特有文本内容
        weixin_specific_texts = [
            "点击上方", "设为星标", "留言请发消息", "长按扫码可关注",
            "继续滑动看下一个", "阅读原文", "微信扫一扫关注该公众号",
            "在小说阅读器中沉浸阅读", "预览时标签不可点"
        ]
        
        # 遍历所有文本节点，移除包含特定文本的节点
        for text in weixin_specific_texts:
            for element in self.soup.find_all(string=lambda t: t and text in t):
                # 检查是否为文本节点
                if element.parent:
                    # 如果是纯文本节点，直接移除
                    if element.parent.name == "p" and element.strip() == element.parent.get_text(strip=True):
                        element.parent.decompose()
                    else:
                        # 否则替换文本
                        new_text = element.replace(text, "")
                        if new_text.strip():
                            element.replace_with(new_text)
                        else:
                            element.extract()
    
    def extract_main_content(self):
        """提取主要内容"""
        if not self.soup:
            self.fetch_webpage()
        
        self.remove_unnecessary_elements()
        
        # 尝试找到主要内容区域
        main_content_selectors = [
            "main", "article", "#main", ".main", ".content", ".article",
            ".post", ".entry", "#content", ".blog-content"
        ]
        
        main_content = None
        for selector in main_content_selectors:
            main_content = self.soup.select_one(selector)
            if main_content:
                break
        
        # 如果找不到特定的内容区域，尝试找到包含最多文本的div
        if not main_content:
            max_text_len = 0
            best_div = None
            for div in self.soup.find_all("div"):
                text_len = len(div.get_text(strip=True))
                if text_len > max_text_len:
                    max_text_len = text_len
                    best_div = div
            main_content = best_div if best_div else self.soup.body
        
        if main_content:
            self.content = self.convert_to_markdown(main_content)
    
    def convert_to_markdown(self, element):
        """将HTML元素转换为Markdown格式"""
        markdown = ""
        
        for child in element.children:
            if child.name is None:
                # 处理文本节点
                text = child.strip()
                if text:
                    markdown += text + "\n"
            elif child.name == "h1":
                markdown += f"# {child.get_text(strip=True)}\n\n"
            elif child.name == "h2":
                markdown += f"## {child.get_text(strip=True)}\n\n"
            elif child.name == "h3":
                markdown += f"### {child.get_text(strip=True)}\n\n"
            elif child.name == "h4":
                markdown += f"#### {child.get_text(strip=True)}\n\n"
            elif child.name == "h5":
                markdown += f"##### {child.get_text(strip=True)}\n\n"
            elif child.name == "h6":
                markdown += f"###### {child.get_text(strip=True)}\n\n"
            elif child.name == "p":
                text = child.get_text(strip=True)
                if text:
                    markdown += f"{text}\n\n"
            elif child.name == "ul":
                for li in child.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        markdown += f"- {text}\n"
                markdown += "\n"
            elif child.name == "ol":
                for i, li in enumerate(child.find_all("li"), 1):
                    text = li.get_text(strip=True)
                    if text:
                        markdown += f"{i}. {text}\n"
                markdown += "\n"
            elif child.name == "blockquote":
                text = child.get_text(strip=True)
                if text:
                    markdown += f"> {text}\n\n"
            elif child.name == "img":
                src = child.get("src", "")
                alt = child.get("alt", "")
                if src:
                    # 转换为绝对URL
                    src = urljoin(self.url, src)
                    markdown += f"![{alt}]({src})\n\n"
            elif child.name == "a":
                href = child.get("href", "")
                text = child.get_text(strip=True)
                if href and text:
                    # 转换为绝对URL
                    href = urljoin(self.url, href)
                    markdown += f"[{text}]({href})"
                else:
                    markdown += text
            elif child.name == "strong" or child.name == "b":
                text = child.get_text(strip=True)
                markdown += f"**{text}**"
            elif child.name == "em" or child.name == "i":
                text = child.get_text(strip=True)
                markdown += f"*{text}*"
            elif child.name == "hr":
                markdown += "---\n\n"
            elif child.name == "br":
                markdown += "\n"
            else:
                # 递归处理其他元素
                markdown += self.convert_to_markdown(child)
        
        return markdown
    
    def clean_markdown(self):
        """清理生成的Markdown，移除多余的空行"""
        # 移除连续的空行（保留最多2个）
        self.content = re.sub(r'\n{3,}', '\n\n', self.content)
        # 移除首尾的空行
        self.content = self.content.strip()
    
    def add_original_link(self):
        """添加原文链接"""
        if self.content:
            self.content += f"\n\n---\n\n**原文链接**：[{self.title}]({self.url})（[取消链接](javascript:void(0))）"
    
    def convert(self):
        """执行完整的转换流程"""
        self.fetch_webpage()
        self.extract_title()
        self.extract_main_content()
        self.clean_markdown()
        self.add_original_link()
        
        return self.content
    
    def save_to_file(self):
        """将转换结果保存到文件"""
        if not self.content:
            self.convert()
        
        # 生成文件名（去除特殊字符）
        filename = re.sub(r'[^\w\u4e00-\u9fa5_-]', '_', self.title)
        filename = f"{filename}_{self.timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.content)
        
        return filename

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python web_to_markdown.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    converter = WebToMarkdownConverter(url)
    
    print(f"正在转换网页: {url}")
    converter.convert()
    
    filename = converter.save_to_file()
    print(f"转换完成，文件已保存为: {filename}")

if __name__ == "__main__":
    main()