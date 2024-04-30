def get_region_base_info(element_name_info, category):
    '''
    Get program element meta-information, eg., variable names, method definitions, and line number/ranges.
    Each category gets different format processing steps.

    element_name_info examples:
        block: src/main/java/org.apache.commons.io.EndianUtils#read(InputStream)$if(475-477)"
        class: src/main/java/org.apache.commons.io.(public)CopyUtils(30)
        method: "src/main/java/org.apache.commons.io.input.Tailer#run()"
        variable: src/main/java/com.puppycrawl.tools.checkstyle.Checker#fireErrors(String, SortedSet)$element:LocalizedMessage(387)
        attribute: src/java/org.apache.commons.io.input.Tailer@(final)(private)end:boolean(70)
                java/compiler/impl/src/com.intellij.packaging.impl.artifacts.ArtifactBySourceFileFinderImpl@myProject:Project(47)

                lucene/core/src/java/org.apache.lucene.index.IndexWriter@config:LiveIndexWriterConfig(339)
                -> 339: private final LiveIndexWriterConfig config;
    '''

    # only "variable" and "attribute" need perfect 'element'.
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
        element = element_name_info.split(".")[-1]
        return element
    else: # or category == "method":
        element = element_name_info.split("#")[-1]
        return element
    
    assert element != None

    tmp = element_name_info.split(".")[-1].split("(")
    line_number = tmp[-1].replace(")", "")
    if "-" in line_number: # special for 'block'
        start_line_number, end_line_number = line_number.split("-")
        return element, start_line_number, end_line_number
    else:
        return element, line_number
