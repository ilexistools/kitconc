# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
class sqlFactory:
    
    def __init__(self):
        pass 
    
    def wordlist(self,lowercase=True):
        if lowercase == True:
            sql="""
            SELECT tolower(word), sum(freq) AS freq
            FROM
            (SELECT word_id,count( word_id) AS freq
            FROM searches 
            GROUP BY word_id) as tb 
            INNER JOIN words ON words.id = tb.word_id
            WHERE regexp(word) = false
            GROUP BY tolower(word)
            ORDER BY freq DESC
            """
        else:
            sql="""
            SELECT word , sum(freq) AS freq
            FROM
            (SELECT word_id,count(word_id) AS freq
            FROM searches 
            GROUP BY word_id) as tb 
            INNER JOIN words ON words.id = tb.word_id
            WHERE regexp(word) = false
            GROUP BY word
            ORDER BY freq DESC
            """
        return sql  
    
    def wtfreq(self,lowercase=True):
        if lowercase == True:
            sql="""
            SELECT tolower(word) AS word, tag, SUM(freq) AS freq
            FROM 
            (SELECT word_id, tag_id, COUNT(*) AS freq
            FROM searches 
            GROUP BY word_id, tag_id) AS tb
            INNER JOIN words ON words.id = tb.word_id
            INNER JOIN tags ON tags.id = tb.tag_id
            WHERE regexp(word) = false
            GROUP BY tolower(word),tag 
            ORDER BY freq DESC
            """
        else:
            sql="""
            SELECT word, tag, SUM(freq) AS freq
            FROM 
            (SELECT word_id, tag_id, COUNT(*) AS freq
            FROM searches 
            GROUP BY word_id, tag_id) AS tb
            INNER JOIN words ON words.id = tb.word_id
            INNER JOIN tags ON tags.id = tb.tag_id
            WHERE regexp(word) = false
            GROUP BY word,tag 
            ORDER BY freq DESC
            """
        return sql 
    
    def wfreqinfiles(self,lowercase=True):
        if lowercase == True:
            sql="""
            SELECT word,COUNT(*) AS freq 
            FROM
            (SELECT tolower(word) AS word,word_id, textfile_id
            FROM searches
            INNER JOIN words ON words.id = searches.word_id
            GROUP BY tolower(word),textfile_id 
            ORDER BY word_id) AS tb
            WHERE regexp(word) = false
            GROUP BY tolower(word)
            ORDER BY freq DESC
            """
        else:
            sql="""
            SELECT word,COUNT(*) AS freq 
            FROM
            (SELECT word AS word,word_id, textfile_id
            FROM searches
            INNER JOIN words ON words.id = searches.word_id
            GROUP BY word,textfile_id 
            ORDER BY word_id) AS tb
            WHERE regexp(word) = false
            GROUP BY word
            ORDER BY freq DESC
            """
        return sql
    
    def kwic_drop_temporary_table(self):
        return """DROP TABLE IF EXISTS temp_kwic"""
    
    def kwic_count_results(self):
        return """SELECT count(*) FROM temp_kwic"""
    
    def kwic_search_node(self,node_length,node,pos,compare_operator,regexp,limit_results):
        if node_length == 1:
            if pos == None:
                if regexp == False:
                    sql="""
                    CREATE TEMPORARY TABLE temp_kwic AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    where word %s '%s' 
                    ORDER BY searches.id
                    %s
                    """ % (compare_operator,node,limit_results)
                else:
                    # with regexp
                    sql="""
                    CREATE TEMPORARY TABLE temp_kwic AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    where regx(word)  
                    ORDER BY searches.id
                    %s
                    """ % (limit_results)
            else:
                if regexp == False:
                    sql="""
                    CREATE TEMPORARY TABLE temp_kwic AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    INNER JOIN tags ON tags.id = searches.tag_id
                    where word %s '%s' AND tag in (%s) 
                    ORDER BY searches.id
                    %s
                    """ % (compare_operator,node,pos,limit_results)
                else:
                    # with regexp
                    sql="""
                    CREATE TEMPORARY TABLE temp_kwic AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    INNER JOIN tags ON tags.id = searches.tag_id
                    where regx(word) AND tag in (%s) 
                    ORDER BY searches.id
                    %s
                    """ % (pos,limit_results)
        # node length is > 1:             
        else:
            if pos == None:
                sql= """
                CREATE TEMPORARY TABLE temp_kwic AS 
                SELECT searches.id
                FROM searches
                INNER JOIN words ON words.id = searches.word_id
                where join_words(word) %s '%s' 
                ORDER BY searches.id
                %s
                """ % (compare_operator,node,limit_results) 
            else:
                sql= """
                CREATE TEMPORARY TABLE temp_kwic AS 
                SELECT searches.id
                FROM searches
                INNER JOIN words ON words.id = searches.word_id
                where join_words(word) %s '%s' AND join_tags(tag) in (%s)
                ORDER BY searches.id
                %s
                """ % (compare_operator,node,pos,limit_results)
        return sql 
    
    def kwic_data(self,hleft,hright):
        sql="""
        SELECT GROUP_CONCAT(word,' ') AS kwic, textfile, tb.id, tb.sentence_id, tb.textfile_id
            FROM searches,
            (SELECT searches.id, searches.textfile_id,searches.sentence_id  
            FROM searches, temp_kwic
            WHERE searches.id = temp_kwic.id 
            ORDER BY searches.id) AS tb 
            INNER JOIN words ON words.id = searches.word_id
            INNER JOIN textfiles ON textfiles.id = tb.textfile_id
            WHERE searches.id BETWEEN tb.id - %s AND tb.id + %s
            GROUP BY tb.id""" % (hleft,hright)
        return sql
    
    def conc_drop_temporary_table(self):
        return """DROP TABLE IF EXISTS temp_conc"""
    
    def conc_count_results(self):
        return """SELECT count(*) FROM temp_conc"""
    
    def conc_search_node(self,node_length,node,pos,compare_operator,regexp,limit_results):
        if node_length == 1:
            if pos == None:
                if regexp == False:
                    sql="""
                    CREATE TEMPORARY TABLE temp_conc AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    where word %s '%s' 
                    ORDER BY searches.id
                    %s
                    """ % (compare_operator,node,limit_results)
                else:
                    # with regexp
                    sql="""
                    CREATE TEMPORARY TABLE temp_conc AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    where regx(word)  
                    ORDER BY searches.id
                    %s
                    """ % (limit_results)
            else:
                if regexp == False:
                    sql="""
                    CREATE TEMPORARY TABLE temp_conc AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    INNER JOIN tags ON tags.id = searches.tag_id
                    where word %s '%s' AND tag in (%s) 
                    ORDER BY searches.id
                    %s
                    """ % (compare_operator,node,pos,limit_results)
                else:
                    # with regexp
                    sql="""
                    CREATE TEMPORARY TABLE temp_conc AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    INNER JOIN tags ON tags.id = searches.tag_id
                    where regx(word) AND tag in (%s) 
                    ORDER BY searches.id
                    %s
                    """ % (pos,limit_results)
        # node length is > 1:             
        else:
            if pos == None:
                sql= """
                CREATE TEMPORARY TABLE temp_conc AS 
                SELECT searches.id
                FROM searches
                INNER JOIN words ON words.id = searches.word_id
                where join_words(word) %s '%s' 
                ORDER BY searches.id
                %s
                """ % (compare_operator,node,limit_results) 
            else:
                sql= """
                CREATE TEMPORARY TABLE temp_conc AS 
                SELECT searches.id
                FROM searches
                INNER JOIN words ON words.id = searches.word_id
                where join_words(word) %s '%s' AND join_tags(tag) in (%s)
                ORDER BY searches.id
                %s
                """ % (compare_operator,node,pos,limit_results)
        return sql
    
    def conc_data(self):
        sql="""
        SELECT GROUP_CONCAT(word,' ') AS conc, textfile, tb.word_pos, tb.sentence_id, tb.textfile_id
            FROM searches,
            (SELECT *  
            FROM searches, temp_conc
            WHERE searches.id = temp_conc.id 
            ORDER BY searches.id) AS tb 
            INNER JOIN words ON words.id = searches.word_id
            INNER JOIN textfiles ON textfiles.id = tb.textfile_id
            WHERE searches.sentence_id = tb.sentence_id 
            GROUP BY tb.id
            ORDER BY tb.id 
            """
        return sql
    
    def coll_drop_temporary_table(self):
        return """DROP TABLE IF EXISTS temp_coll"""
    
    def coll_count_results(self):
        return """SELECT count(*) FROM temp_coll"""
    
    def coll_search_node(self,node_length,node,pos,compare_operator,regexp,limit_results):
        if node_length == 1:
            if pos == None:
                if regexp == False:
                    sql="""
                    CREATE TEMPORARY TABLE temp_coll AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    where word %s '%s' 
                    ORDER BY searches.id
                    %s
                    """ % (compare_operator,node,limit_results)
                else:
                    # with regexp
                    sql="""
                    CREATE TEMPORARY TABLE temp_coll AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    where regx(word)  
                    ORDER BY searches.id
                    %s
                    """ % (limit_results)
            else:
                if regexp == False:
                    sql="""
                    CREATE TEMPORARY TABLE temp_coll AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    INNER JOIN tags ON tags.id = searches.tag_id
                    where word %s '%s' AND tag in (%s) 
                    ORDER BY searches.id
                    %s
                    """ % (compare_operator,node,pos,limit_results)
                else:
                    # with regexp
                    sql="""
                    CREATE TEMPORARY TABLE temp_coll AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    INNER JOIN tags ON tags.id = searches.tag_id
                    where regx(word) AND tag in (%s) 
                    ORDER BY searches.id
                    %s
                    """ % (pos,limit_results)
        # node length is > 1:             
        else:
            if pos == None:
                sql= """
                CREATE TEMPORARY TABLE temp_coll AS 
                SELECT searches.id
                FROM searches
                INNER JOIN words ON words.id = searches.word_id
                where join_words(word) %s '%s' 
                ORDER BY searches.id
                %s
                """ % (compare_operator,node,limit_results) 
            else:
                sql= """
                CREATE TEMPORARY TABLE temp_coll AS 
                SELECT searches.id
                FROM searches
                INNER JOIN words ON words.id = searches.word_id
                where join_words(word) %s '%s' AND join_tags(tag) in (%s)
                ORDER BY searches.id
                %s
                """ % (compare_operator,node,pos,limit_results)
        return sql
    
    def coll_wordlist(self,lowercase=True):
        if lowercase == True:
            sql="""
            SELECT tolower(word), sum(freq) AS freq
            FROM
            (SELECT word_id,count( word_id) AS freq
            FROM searches 
            GROUP BY word_id) as tb 
            INNER JOIN words ON words.id = tb.word_id
            GROUP BY tolower(word)
            ORDER BY freq DESC
            """
        else:
            sql="""
            SELECT word , sum(freq) AS freq
            FROM
            (SELECT word_id,count(word_id) AS freq
            FROM searches 
            GROUP BY word_id) as tb 
            INNER JOIN words ON words.id = tb.word_id
            GROUP BY word
            ORDER BY freq DESC
            """
        return sql 
    
    def coll_left_data(self,lowercase,node_length,left_span,coll_pos):
        if coll_pos != None:
            coll_pos = ' AND searches.tag_id IN (' + coll_pos + ') '
        else:
            coll_pos = ''
            
        if node_length == 1:
            if lowercase == True:
                sql="""
                SELECT tolower(word),COUNT(lower(word)) AS freq
                    FROM searches,
                    (SELECT *  
                    FROM searches, temp_coll
                    WHERE searches.id = temp_coll.id 
                    ORDER BY searches.id) AS tb 
                    INNER JOIN words ON words.id = searches.word_id
                    WHERE searches.id BETWEEN (tb.id  - %s) AND (tb.id  -1) %s  
                    GROUP BY tolower(word)
                    ORDER BY freq DESC 
                    """ % (left_span, coll_pos) 
            else:
                sql="""
                SELECT word,COUNT(word) AS freq
                    FROM searches,
                    (SELECT *  
                    FROM searches, temp_coll
                    WHERE searches.id = temp_coll.id 
                    ORDER BY searches.id) AS tb 
                    INNER JOIN words ON words.id = searches.word_id
                    WHERE searches.id BETWEEN (tb.id  - %s) AND (tb.id  -1) %s  
                    GROUP BY word
                    ORDER BY freq DESC 
                    """ % (left_span, coll_pos)
        else:
            # for more than 1 word, tb.id comes from the last word in the n-gram
            # we use fix to set tb.id for the first word in the n-gram
            fix = node_length - 1 
            if lowercase == True:
                sql="""
                SELECT tolower(word),COUNT(lower(word)) AS freq
                    FROM searches,
                    (SELECT *  
                    FROM searches, temp_coll
                    WHERE searches.id = temp_coll.id 
                    ORDER BY searches.id) AS tb 
                    INNER JOIN words ON words.id = searches.word_id
                    WHERE searches.id BETWEEN ((tb.id - %s) - %s) AND ((tb.id - %s) -1) %s   
                    GROUP BY tolower(word)
                    ORDER BY freq DESC 
                    """ % (fix,left_span,fix,coll_pos)
            else:
                sql="""
                SELECT word,COUNT(word) AS freq
                    FROM searches,
                    (SELECT *  
                    FROM searches, temp_coll
                    WHERE searches.id = temp_coll.id 
                    ORDER BY searches.id) AS tb 
                    INNER JOIN words ON words.id = searches.word_id
                    WHERE searches.id BETWEEN ((tb.id - %s) - %s) AND ((tb.id - %s) -1) %s    
                    GROUP BY word
                    ORDER BY freq DESC 
                    """ % (fix,left_span,fix,coll_pos)
        return sql
    
    def coll_right_data(self,lowercase,node_length,right_span,coll_pos):
        if coll_pos != None:
            coll_pos = ' AND searches.tag_id IN (' + coll_pos + ') '
        else:
            coll_pos = ''
        if node_length == 1:
            if lowercase == True:
                sql="""
                SELECT tolower(word),COUNT(lower(word)) AS freq
                    FROM searches,
                    (SELECT *  
                    FROM searches, temp_coll
                    WHERE searches.id = temp_coll.id 
                    ORDER BY searches.id) AS tb 
                    INNER JOIN words ON words.id = searches.word_id
                    WHERE searches.id BETWEEN (tb.id + 1) AND (tb.id  + %s)  %s  
                    GROUP BY tolower(word)
                    ORDER BY freq DESC 
                    """ % (right_span, coll_pos)
            else:
                sql="""
                SELECT word,COUNT(word) AS freq
                    FROM searches,
                    (SELECT *  
                    FROM searches, temp_coll
                    WHERE searches.id = temp_coll.id 
                    ORDER BY searches.id) AS tb 
                    INNER JOIN words ON words.id = searches.word_id
                    WHERE searches.id BETWEEN (tb.id + 1) AND (tb.id  + %s) %s  
                    GROUP BY word
                    ORDER BY freq DESC 
                    """ % (right_span,coll_pos)
        else:
            if lowercase == True:
                sql="""
                SELECT tolower(word),COUNT(lower(word)) AS freq
                    FROM searches,
                    (SELECT *  
                    FROM searches, temp_coll
                    WHERE searches.id = temp_coll.id 
                    ORDER BY searches.id) AS tb 
                    INNER JOIN words ON words.id = searches.word_id
                    WHERE searches.id BETWEEN (tb.id + 1) AND (tb.id + %s) %s  
                    GROUP BY tolower(word)
                    ORDER BY freq DESC 
                    """ % (right_span,coll_pos)
            else:
                sql="""
                SELECT word,COUNT(word) AS freq
                    FROM searches,
                    (SELECT *  
                    FROM searches, temp_coll
                    WHERE searches.id = temp_coll.id 
                    ORDER BY searches.id) AS tb 
                    INNER JOIN words ON words.id = searches.word_id
                    WHERE searches.id BETWEEN (tb.id + 1) AND (tb.id + %s) %s   
                    GROUP BY word
                    ORDER BY freq DESC 
                    """ % (right_span,coll_pos)
                    
        return sql
    
    def clusters_searches_all(self,lowercase):
        if lowercase == True:
            sql="""
            SELECT tolower(word),tag_id, textfile_id
            FROM searches
            INNER JOIN words ON words.id = searches.word_id
            ORDER BY searches.id 
            """
        else:
            sql="""
            SELECT word,tag_id, textfile_id
            FROM searches
            INNER JOIN words ON words.id = searches.word_id
            ORDER BY searches.id 
            """
        return sql
    
    def ngrams_search_by_file(self,file_id,lowercase):
        if lowercase == True:
            sql=""" 
            SELECT tolower(word),tag_id 
            FROM searches
            INNER JOIN words ON words.id = searches.word_id
            WHERE textfile_id = %s
            ORDER BY searches.id""" % file_id
        else:
            sql=""" 
            SELECT word,tag_id 
            FROM searches
            INNER JOIN words ON words.id = searches.word_id
            WHERE textfile_id = %s
            ORDER BY searches.id""" % file_id
            
        return sql 
    
    def ngrams_searches_all(self):
        sql=""" 
        SELECT word_id,tag_id 
        FROM searches
        ORDER BY searches.id 
        """
        return sql 
    
    def ngrams_one_char(self):
        sql = """
        SELECT id, word
        FROM words
        WHERE length(word) = 1
        """
        return sql 
    
    def dispersion_drop_temporary_table(self):
        return """DROP TABLE IF EXISTS temp_disp"""
    
    def dispersion_count_results(self):
        return """SELECT count(*) FROM temp_disp"""
    
    def dispersion_search_node(self,node_length,node,pos,compare_operator,regexp,limit_results):
        if node_length == 1:
            if pos == None:
                if regexp == False:
                    sql="""
                    CREATE TEMPORARY TABLE temp_disp AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    where word %s '%s' 
                    ORDER BY searches.id
                    %s
                    """ % (compare_operator,node,limit_results)
                else:
                    # with regexp
                    sql="""
                    CREATE TEMPORARY TABLE temp_disp AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    where regx(word)  
                    ORDER BY searches.id
                    %s
                    """ % (limit_results)
            else:
                if regexp == False:
                    sql="""
                    CREATE TEMPORARY TABLE temp_disp AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    INNER JOIN tags ON tags.id = searches.tag_id
                    where word %s '%s' AND tag in (%s) 
                    ORDER BY searches.id
                    %s
                    """ % (compare_operator,node,pos,limit_results)
                else:
                    # with regexp
                    sql="""
                    CREATE TEMPORARY TABLE temp_disp AS 
                    SELECT searches.id
                    FROM searches
                    INNER JOIN words ON words.id = searches.word_id
                    INNER JOIN tags ON tags.id = searches.tag_id
                    where regx(word) AND tag in (%s) 
                    ORDER BY searches.id
                    %s
                    """ % (pos,limit_results)
        # node length is > 1:             
        else:
            if pos == None:
                sql= """
                CREATE TEMPORARY TABLE temp_disp AS 
                SELECT searches.id
                FROM searches
                INNER JOIN words ON words.id = searches.word_id
                where join_words(word) %s '%s' 
                ORDER BY searches.id
                %s
                """ % (compare_operator,node,limit_results) 
            else:
                sql= """
                CREATE TEMPORARY TABLE temp_disp AS 
                SELECT searches.id
                FROM searches
                INNER JOIN words ON words.id = searches.word_id
                where join_words(word) %s '%s' AND join_tags(tag) in (%s)
                ORDER BY searches.id
                %s
                """ % (compare_operator,node,pos,limit_results)
        return sql
    
    def dispersion_count_by_file(self):
        sql="""
            SELECT textfile_id,COUNT(*) AS freq
            FROM searches 
            GROUP BY textfile_id
        """
        return sql
    
    def dispersion_data(self):
        sql="""
            select textfile_id,loc_id
            from searches, (select * from temp_disp order by id) as tb
            where searches.id = tb.id 
            
            """
        return sql
    
    def dispersion_filenames(self):
        sql="""
            SELECT * FROM textfiles
            """
        return sql
    
    
    def keywords_dispersion_drop_temporary_table(self):
        return """DROP TABLE IF EXISTS temp_disp"""
    
    def keywords_dispersion_count_results(self):
        return """SELECT count(*) FROM temp_disp"""
    
    def keywords_dispersion_count_by_file(self):
        sql="""
            SELECT textfile_id,COUNT(*) AS freq
            FROM searches 
            GROUP BY textfile_id
        """
        return sql
    
    def keywords_dispersion_searches(self, lowercase):
        if lowercase == True:
            sql="""
            CREATE TEMPORARY TABLE temp_disp AS 
                        SELECT searches.id
                        FROM searches
                        INNER JOIN words ON words.id = searches.word_id
                        WHERE match(lower(word))
                        ORDER BY searches.id
            """
        else:
            sql="""
            CREATE TEMPORARY TABLE temp_disp AS 
                        SELECT searches.id
                        FROM searches
                        INNER JOIN words ON words.id = searches.word_id
                        WHERE match(word)
                        ORDER BY searches.id
            """
        return sql 
    
    def keywords_dispersion_data(self):
        sql="""
            select textfile_id,loc_id,word
            from searches, (select * from temp_disp order by id) as tb
            INNER JOIN words ON words.id = searches.word_id
            where searches.id = tb.id 
            """
        return sql



    
    
            
            
        
    
