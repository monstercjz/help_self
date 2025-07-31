--configFilePath = "J:\\0911\\分机账号.txt"这个文件的格式是32401:雷ぃ傷う|冰璐つ筱馨|べ杨。|べ陈。|べ明°|べ黄。，
--冒号前面作为复制源文件夹名字sourceFolder，冒号后面作为寻找的名字字符串集合，用|串接在一起的
--这个程序里，在rootDestinationFolder这个目录里，根据源文件夹名字sourceFolder找到每个文件夹，并且将符合名字条件的复制到rootDestinationFolder下面的all目录下
--在遍历的时候，应该排除all这个文件夹
local lfs = require("lfs")

-- 定义根目录
local sourceFolder = "D:\\天龙相关\\临时处理\\"
local rootDestinationFolder = "D:\\天龙相关\\临时处理\\"
local configFilePath = "D:\\天龙相关\\临时处理\\分机账号.txt"

-- 从文件中读取搜索名称字符串
local function readConfigFile(filePath)
    local file = io.open(filePath, "r")
    if not file then
        error("无法打开文件: " .. filePath)
    end
    local lines = {}
    for line in file:lines() do
        table.insert(lines, line)
    end
    file:close()
    return lines
end

-- 分割字符串
local function splitString(inputstr, sep)
    sep = sep or "%s"
    local t = {}
    for str in string.gmatch(inputstr, "([^" .. sep .. "]+)") do
        table.insert(t, str)
    end
    return t
end

-- 检查并创建目标目录
local function createDirectory(path)
    if not lfs.attributes(path, "mode") then
        print("创建目录: " .. path)
        lfs.mkdir(path)
    else
        print("目录已存在: " .. path)
    end
end

-- 递归创建父目录
local function createParentFolders(folderPath)
    if folderPath == "" or folderPath == "." or folderPath == ".." then return end
    local parentFolder = folderPath:match("(.*[\\/])[^\\/]*$")
    if parentFolder and parentFolder ~= folderPath and not lfs.attributes(parentFolder, "mode") then
        createParentFolders(parentFolder)
        lfs.mkdir(parentFolder)
    end
end

-- 复制文件或目录
local function copyFileOrDir(srcPath, destPath)
    createParentFolders(destPath)
    if lfs.attributes(srcPath, "mode") == "directory" then
        os.execute("xcopy \"" .. srcPath .. "\" \"" .. destPath .. "\" /E /I /Y")
    else
        os.execute("copy \"" .. srcPath .. "\" \"" .. destPath .. "\" /Y")
    end
end

-- 递归复制文件和文件夹
local function recurseCopyFilesAndFolders(folder, searchName, destFolder)
    print("遍历目录: " .. folder)
    for file in lfs.dir(folder) do
        if file ~= "." and file ~= ".." and file ~= "all" then -- 排除 "all" 文件夹
            local srcPath = folder .. "\\" .. file
            local destPath = destFolder .. "\\" .. file
            local attr = lfs.attributes(srcPath)
            if attr.mode == "directory" then
                print("检查目录: " .. srcPath)
                if string.find(file, searchName) then
                    print("匹配目录: " .. srcPath)
                    if not lfs.attributes(destPath, "mode") then
                        createDirectory(destPath)
                    end
                    copyFileOrDir(srcPath, destPath)
                    recurseCopyFilesAndFolders(srcPath, searchName, destPath)
                end
            elseif attr.mode == "file" then
                print("检查文件: " .. srcPath)
                if string.find(file, searchName) then
                    print("匹配文件: " .. srcPath)
                    copyFileOrDir(srcPath, destPath)
                end
            end
        end
    end
end

-- 处理单个配置项
local function processConfigItem(configLine)
    local targetFolderName, searchNamesStr = configLine:match("([^:]+):(.+)")
    if not targetFolderName or not searchNamesStr then
        error("配置文件格式错误: " .. configLine)
    end

    local sourceSubFolder = sourceFolder .. targetFolderName .. "\\角色配置"
    local searchNames = splitString(searchNamesStr, "|")

    local docDestinationFolder = rootDestinationFolder .. "\\all" -- 目标目录改为 all
    createDirectory(docDestinationFolder)

    for _, searchName in ipairs(searchNames) do
        print("处理搜索名称: " .. searchName)
        recurseCopyFilesAndFolders(sourceSubFolder, searchName, docDestinationFolder)
    end
end

-- 主函数
local function main()
    local configLines = readConfigFile(configFilePath)
    for _, line in ipairs(configLines) do
        print("处理配置行: " .. line)
        processConfigItem(line)
    end
    print("复制完成")
end

-- 运行主函数
main()