/**********************************************************************
* Copyright 2023-xxxx Nriet Co., Ltd.
* All right reserved. See COPYRIGHT for detailed Information
*
* Alternatively, you may use this file under the terms of the NRT license
* as follows:
**
* "Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are
* met:
*   * Redistributions of source code must retain the above copyright
*     notice, this list of conditions and the following disclaimer.
*   * Redistributions in binary form must reproduce the above copyright
*     notice, this list of conditions and the following disclaimer in
*     the documentation and/or other materials provided with the
*     distribution.
*   * Neither the name of The NRT Company Ltd nor the names of its
*     contributors may be used to endorse or promote products derived
*     from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
* "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
* LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
* A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
* OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
* SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
* LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
* DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
* THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
*
* File:INIParser.cpp
* Author:Nriet
* time 2023-05-17
*************************************************************************/
#include <IniParser/INIParser.h>

/**
 * @brief TrimString
 * @param str
 * @return
 */
// 对传入的字符串 str 进行修剪（去除空格和回车符 \r），并返回修剪后的字符串的引用
string &TrimString(string &str)
{
    string::size_type pos = 0;
    while (str.npos != (pos = str.find(" ")))
    {
        str.erase(pos, 1);
    }
//        str = str.replace(pos, pos + 1, "");

    while (str.npos != (pos = str.find('\r')))
    {
        str = str.replace(pos, pos + 1, "");
    }

    return str;
}

/**
 * @brief INIParser::ReadINI
 * @param path
 * @return
 */
int INIParser::ReadINI(string path)
{
    ifstream in_conf_file(path.c_str());
    if (!in_conf_file)
    {
        return 0;
    }
    string str_line = "";
    string str_root = "";
    vector<ININode> vec_ini;
    while (getline(in_conf_file, str_line))
    {
        string::size_type left_pos = 0;
        string::size_type right_pos = 0;
        string::size_type equal_div_pos = 0;
        string str_key = "";
        string str_value = "";

        TrimString(str_line);

        if (str_line.empty())
        {
            continue;
        }

        if (str_line.front() == ';')
        {
            continue;
        }

        if ((str_line.npos != (left_pos = str_line.find("["))) && (str_line.npos != (right_pos = str_line.find("]"))))
        {
            //cout << str_line.substr(left_pos+1, right_pos-1) << endl;
            str_root = str_line.substr(left_pos + 1, right_pos - 1);
            std::transform(str_root.begin(), str_root.end(), str_root.begin(), (int(*)(int))tolower);
        }

        if (str_line.npos != (equal_div_pos = str_line.find("=")))
        {
            str_key = str_line.substr(0, equal_div_pos);
            str_value = str_line.substr(equal_div_pos + 1, str_line.size() - 1);
            str_key = TrimString(str_key);
            std::transform(str_key.begin(), str_key.end(), str_key.begin(), (int(*)(int))tolower);
            str_value = TrimString(str_value);
            //cout << str_key << "=" << str_value << endl;
        }

        if ((!str_root.empty()) && (!str_key.empty()) && (!str_value.empty()))
        {
            this->SetValue(str_root, str_key, str_value);
//            ININode ini_node(str_root, str_key, str_value);
//            vec_ini.push_back(ini_node);
            //cout << vec_ini.size() << endl;
        }
    }
    in_conf_file.close();
    in_conf_file.clear();

//    //vector convert to map
//    map<string, string> map_tmp;
//    for (vector<ININode>::iterator itr = vec_ini.begin(); itr != vec_ini.end(); ++itr)
//    {
//        map_tmp.insert(pair<string, string>(itr->root, ""));
//    }

//    for (vector<ININode>::iterator sub_itr = vec_ini.begin(); sub_itr != vec_ini.end(); ++sub_itr)
//    {
//        this->SetValue(sub_itr->root,sub_itr->key,sub_itr->value);
//    }

    return 1;
}

/**
 * @brief INIParser::GetValue
 * @param root
 * @param key
 * @return
 */
string INIParser::GetValue(string root, string key)
{
    std::transform(root.begin(), root.end(), root.begin(), (int(*)(int))tolower);
    std::transform(key.begin(), key.end(), key.begin(), (int(*)(int))tolower);
    map<string, SubNode>::iterator itr = map_ini.find(root);
    if (itr != map_ini.end())
    {
        map<string, string>::iterator sub_itr = itr->second.sub_node.find(key);
        if (sub_itr != itr->second.sub_node.end())
            if (!(sub_itr->second).empty())
            {
                return sub_itr->second;
            }
    }

    return "";
}

/**
 * @brief INIParser::GetGroup
 * @param root
 * @return
 */
map<string, string> INIParser::GetGroup(string root)
{
    std::transform(root.begin(), root.end(), root.begin(), (int(*)(int))tolower);
    map<string, SubNode>::iterator itr = map_ini.find(root);
    if (itr != map_ini.end())
    {
        return itr->second.sub_node;
    }
    map<string, string> ret;
    return ret;
}

/**
 * @brief INIParser::WriteINI
 * @param path
 * @return
 */
int INIParser::WriteINI(string path)
{
    ofstream out_conf_file(path.c_str());
    if (!out_conf_file)
    {
        return -1;
    }

    //cout << map_ini.size() << endl;
    for (map<string, SubNode>::iterator itr = map_ini.begin(); itr != map_ini.end(); ++itr)
    {
        //cout << itr->first << endl;
        out_conf_file << "[" << itr->first << "]\n\r" << endl;
        for (map<string, string>::iterator sub_itr = itr->second.sub_node.begin(); sub_itr != itr->second.sub_node.end(); ++sub_itr)
        {
            //cout << sub_itr->first << "=" << sub_itr->second << endl;
            out_conf_file << sub_itr->first << "=" << sub_itr->second << "\n\r" << endl;
        }
    }

    out_conf_file.close();
    out_conf_file.clear();
    return 1;
}

/**
 * @brief INIParser::Travel
 */
void INIParser::Travel()
{
    for (map<string, SubNode>::iterator itr = this->map_ini.begin(); itr != this->map_ini.end(); ++itr)
    {
        //root
        cout << "[" << itr->first << "]" << endl;
        for (map<string, string>::iterator itr1 = itr->second.sub_node.begin(); itr1 != itr->second.sub_node.end(); ++itr1)
        {
            cout << "   " << itr1->first << " = " << itr1->second << endl;
        }
    }
}

/**
 * @brief INIParser::SetValue
 * @param root
 * @param key
 * @param value
 * @return
 */
vector<ININode>::size_type INIParser::SetValue(string root, string key, string value)
{
    std::transform(root.begin(), root.end(), root.begin(), (int(*)(int))tolower);
    std::transform(key.begin(), key.end(), key.begin(), (int(*)(int))tolower);
    map<string, SubNode>::iterator itr = map_ini.find(root);
    if (map_ini.end() != itr)
    {
        //itr->second.sub_node.insert(pair<string, string>(key, value));
        // update key
        auto key_itr = itr->second.sub_node.find(key);
        if (itr->second.sub_node.end() != key_itr)
        {
            itr->second.sub_node[key] = value;
        }
        else
        {
            itr->second.InsertElement(key, value);
        }
    }
    else
    {
        SubNode sn;
        sn.InsertElement(key, value);
        // add a new key
        map_ini.insert(pair<string, SubNode>(root, sn));
    }

    return map_ini.size();
}




/*
vector<ININode>::size_type INIParser::SetValue(string root, string key, string value)
{
    std::transform(root.begin(),root.end(),root.begin(),(int(*)(int))tolower);
    std::transform(key.begin(),key.end(),key.begin(),(int(*)(int))tolower);
    map<string, SubNode>::iterator itr = map_ini.find(root);
    if (map_ini.end() != itr)
    {
        //itr->second.sub_node.insert(pair<string, string>(key, value));
        // update key
        auto key_itr = itr->second.sub_node.find(key);
        if (itr->second.sub_node.end() != key_itr)
        {
            itr->second.sub_node[key] = value;
        }
        else
        {
            itr->second.InsertElement(key, value);
        }
    }
    else
    {
        SubNode sn;
        sn.InsertElement(key, value);
        // add a new key
        map_ini.insert(pair<string, SubNode>(root, sn));
    }

    return map_ini.size();
}
*/
