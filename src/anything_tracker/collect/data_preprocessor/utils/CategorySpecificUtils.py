def get_region_base_info(element_name_info, category):
    '''
    Get program element meta-information, eg., variable names, method definitions, and line number/ranges.
    Each category gets different format processing steps.

    element_name_info examples:
        block: src/main/java/org.apache.commons.io.EndianUtils#read(InputStream)$if(475-477)"
        class: src/main/java/org.apache.commons.io.(public)CopyUtils(30)
                okhttp-urlconnection/src/main/java/okhttp3.(public)(final)JavaNetAuthenticator(26)'
                spring-context/src/main/java/org.springframework.context.annotation.(package)ConfigurationClassParser(83)
        method: "src/main/java/org.apache.commons.io.input.Tailer#run()"
        variable: src/main/java/com.puppycrawl.tools.checkstyle.Checker#fireErrors(String, SortedSet)$element:LocalizedMessage(387)
        attribute: src/java/org.apache.commons.io.input.Tailer@(final)(private)end:boolean(70)
                java/compiler/impl/src/com.intellij.packaging.impl.artifacts.ArtifactBySourceFileFinderImpl@myProject:Project(47)

                lucene/core/src/java/org.apache.lucene.index.IndexWriter@config:LiveIndexWriterConfig(339)
                -> 339: private final LiveIndexWriterConfig config;
    '''

    element = None
    if category == "block":
        # coarse-grained result, follows further processing
        element = element_name_info.split("#")[-1]
    elif category == "variable":
        element = element_name_info.split("$")[1].split(":")[0]
    elif category == "attribute":
        splits_tmp = element_name_info.split(":")[0]
        if ")" in splits_tmp:
            element = splits_tmp.split(")")[-1]
        else:
            element = splits_tmp.split("@")[1]
    elif category == "class": 
        element = element_name_info.split(".")[-1] # like (public)()CopyUtils(30)
        tmp = element.split(")")
        accessor = tmp[0].replace("(", "")
        if accessor not in ["public", "private", "default", "protected", "package"]:
            # 1 special case: okhttp/src/main/java/okhttp3.internal.http2.(final)Http2Codec(53)
            # the data creators missed the "public" for it.
            print(element_name_info)
            accessor = ""
        class_name = tmp[-2].split("(")[0]
        # if needed, return the line number
        return class_name, accessor
    else: # or category == "method":
        element = element_name_info.split("#")[-1] # like run(), or run(String)
        tmp = element.split("(")
        method_name = tmp[0]
        parameter_types = tmp[1].replace(")", "")
        return method_name, parameter_types
    
    assert element != None

    tmp = element_name_info.split(".")[-1].split("(")
    line_number = tmp[-1].replace(")", "")
    if "-" in line_number: # special for 'block'
        start_line_number, end_line_number = line_number.split("-")
        return element, start_line_number, end_line_number
    else:
        return element, line_number
