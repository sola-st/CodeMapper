## Manually collected 30 change maps

These 30 change maps covers 7 different programming languages: Python, Java, Go, JavaScript, C++, PHP, Ruby. There are also several change maps is about yaml files, JSON files, and markdown files. 

The change details are stored in a JSON file.
#### Character level ranges (old_range, new_range):   
[start_line_number, start_character_index, end_line_number,  end_character_index]      
**All the range numbers starts at 1.*  
#### The old range can specified to anywhere you want.  
For example:
```
12 if mark == True:
13    assert results != ""
```
changed **mark** to **final_mark**
```
15 if final_mark == True:
16    assert results != ""
```
The old range can be   
* [12, 4, 12, 8], exactly the character range for **mark**.
* [12, 1, 12, 15], the entire line 12.
* [12, 1, 13, 24], the entire if block (line 12 and 13).
* [13, 1, 13, 24], the entire line 13, even it hasn't changed.
* ...



