为什么 Metadata Filter 对企业 RAG 特别重要？

假设公司有：

tenant-A
tenant-B
tenant-C

用户属于：

tenant-A

你绝对不能：

整个知识库搜索
 ↓
返回结果
 ↓
再判断权限

因为可能已经发生：

数据泄露

正确设计应该接近：

Query
 ↓
Tenant / Permission Filter
 ↓
Retrieval
 ↓
Top K

也就是：

权限控制

应该成为 Retrieval 的一部分。