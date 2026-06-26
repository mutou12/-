"""
预定义 SPARQL 查询集合

SPARQL 对三元组图的作用等同于 SQL 对关系表，
但能自然表达跨跳图遍历、路径查询、模糊语义匹配等。
"""

# ── Q1: 列出所有 ML 框架及其 stars ────────────────────────────────────────────
Q_ML_FRAMEWORKS = """
PREFIX tkb: <http://example.org/tech-kb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?name ?stars ?releaseYear
WHERE {
    ?fw a tkb:MLFramework ;
        rdfs:label ?name .
    OPTIONAL { ?fw tkb:githubStars ?stars . }
    OPTIONAL { ?fw tkb:releaseYear ?releaseYear . }
}
ORDER BY DESC(?stars)
"""

# ── Q2: 查找与 Python 相关的所有技术（一跳 usedWith） ─────────────────────────
Q_PYTHON_ECOSYSTEM = """
PREFIX tkb: <http://example.org/tech-kb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?name ?type
WHERE {
    tkb:Python tkb:usedWith ?tech .
    ?tech rdfs:label ?name .
    ?tech a ?type .
    FILTER(?type != <http://www.w3.org/2002/07/owl#NamedIndividual>)
}
ORDER BY ?name
"""

# ── Q3: 类层次结构：列出所有 Database 子类及其实例数 ─────────────────────────
Q_DATABASE_HIERARCHY = """
PREFIX tkb: <http://example.org/tech-kb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?subClass (COUNT(?instance) AS ?count)
WHERE {
    ?subClass rdfs:subClassOf tkb:Database .
    OPTIONAL { ?instance a ?subClass . }
    FILTER(?subClass != owl:Nothing)
}
GROUP BY ?subClass
ORDER BY DESC(?count)
"""

# ── Q4: 找出所有具有竞争关系的技术对 ─────────────────────────────────────────
Q_COMPETITORS = """
PREFIX tkb: <http://example.org/tech-kb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?a_name ?b_name
WHERE {
    ?a tkb:competitorOf ?b .
    ?a rdfs:label ?a_name .
    ?b rdfs:label ?b_name .
    FILTER(STR(?a) < STR(?b))  # 去重：只保留 a<b 一侧
}
ORDER BY ?a_name
"""

# ── Q5: 给定技术，推荐配合使用的数据库（两跳图遍历）──────────────────────────
# 注：不依赖推理，直接枚举数据库子类（VectorDatabase、GraphDatabase等）
Q_RECOMMEND_DB = """
PREFIX tkb: <http://example.org/tech-kb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?dbName ?dbDesc
WHERE {
    {
        tkb:PyTorch tkb:usedWith ?db .
        ?db a ?dbType .
        VALUES ?dbType { tkb:VectorDatabase tkb:GraphDatabase tkb:RelationalDatabase }
    } UNION {
        tkb:PyTorch tkb:usedWith ?middle .
        ?middle tkb:usedWith ?db .
        ?db a ?dbType .
        VALUES ?dbType { tkb:VectorDatabase tkb:GraphDatabase tkb:RelationalDatabase }
    }
    ?db rdfs:label ?dbName .
    OPTIONAL { ?db tkb:description ?dbDesc . }
}
ORDER BY ?dbName
"""

# ── Q6: 按 license 统计技术数量 ───────────────────────────────────────────────
# 注：枚举所有技术具体子类，因无推理环境下子类实例不被视为父类成员
Q_LICENSE_STATS = """
PREFIX tkb: <http://example.org/tech-kb#>

SELECT ?license (COUNT(?tech) AS ?count)
WHERE {
    ?tech a ?techType .
    VALUES ?techType {
        tkb:ProgrammingLanguage tkb:MLFramework tkb:WebFramework
        tkb:VectorDatabase tkb:GraphDatabase tkb:RelationalDatabase
    }
    ?tech tkb:license ?license .
}
GROUP BY ?license
ORDER BY DESC(?count)
"""

# ── Q7: 找出从某技术出发，所有 builtOn 路径（Property Path） ─────────────────
Q_DEPENDENCY_CHAIN = """
PREFIX tkb: <http://example.org/tech-kb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?name
WHERE {
    tkb:Transformers tkb:builtOn+ ?dep .
    ?dep rdfs:label ?name .
}
ORDER BY ?name
"""

# ── Q8: 全文搜索描述中包含特定词的技术 ───────────────────────────────────────
Q_SEARCH_BY_DESC = """
PREFIX tkb: <http://example.org/tech-kb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?name ?desc
WHERE {
    ?tech rdfs:label ?name ;
          tkb:description ?desc .
    FILTER(CONTAINS(LCASE(?desc), "向量"))
}
"""

# ── Q9: 查找由特定组织创建的所有技术 ─────────────────────────────────────────
Q_BY_CREATOR = """
PREFIX tkb: <http://example.org/tech-kb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?techName ?type ?year
WHERE {
    ?tech tkb:createdBy ?org .
    ?org rdfs:label "Meta" .
    ?tech rdfs:label ?techName .
    ?tech a ?type .
    OPTIONAL { ?tech tkb:releaseYear ?year . }
    FILTER(?type != <http://www.w3.org/2002/07/owl#NamedIndividual>)
}
"""
