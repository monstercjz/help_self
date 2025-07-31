--在2.0的基础上，把输出路径也做了动态处理，由原来的日期目录，变成了D:\\天龙相关\\20241111\\id\\游戏账号\\id.txt
local luacom = require('luacom')
local io = require("io")
local os = require("os")
local lfs = require("lfs")  -- 引入 lfs 模块用于文件系统操作

-- 获取今天的日期并格式化为 mmdd 格式
local today = os.date("%m%d")

-- 创建 Excel 应用程序对象
local excel = luacom.CreateObject("Excel.Application")
excel.Visible = false

-- 打开 Excel 工作簿
local workbook_path = "D:\\天龙相关\\天龙账号5.xlsm"
-- 读取输入文件路径
local inputFilePath = "D:\\天龙相关\\临时处理\\分机账号.txt"
-- 设置输出文件路径的前缀
local outputDir = "D:\\天龙相关\\临时处理\\"
print(workbook_path)
local workbook
if io.open(workbook_path, "r") then
    workbook = excel.Workbooks:Open(workbook_path)
else
    workbook = excel.Workbooks:Add()
    print("文件不存在: " .. workbook_path)
    return
end

local worksheet = workbook.Worksheets("全部成员")
if worksheet then
    print("全部成员 存在")
else
    print("全部成员 不存在")
    return
end

print(worksheet.UsedRange.Rows.Count .. "行")

-- 打开输入文件
local inputFile = io.open(inputFilePath, "r")
if not inputFile then
    print("无法打开输入文件: " .. inputFilePath)
    return
end

-- 读取 A 列的数据
local lastRow = worksheet.UsedRange.Rows.Count
print("最后一行: " .. lastRow)

local excelData = {}
for i = 1, lastRow do
    local memberName = worksheet.Cells(i, 2).Value2
    local accountInfo = worksheet.Cells(i, 6).Value2
    excelData[memberName] = accountInfo
end

-- 处理每一行
local line
while true do
    line = inputFile:read("*line")
    if not line then break end

    print("读取行: " .. line)

    local id, membersStr = string.match(line, "^(%d+):(.+)$")
    if not id or not membersStr then
        print("无效的行格式: " .. line)
        -- 跳过当前行
        break
    end

    local members = {}
    for member in string.gmatch(membersStr, "[^|]+") do
        table.insert(members, member)
    end

    print("成员组合: " .. table.concat(members, ", "))

    local accountInfo = ""
    for _, member in ipairs(members) do
        if excelData[member] then
            if accountInfo == "" then
                accountInfo = excelData[member]
            else
                accountInfo = accountInfo .. "\n" .. excelData[member]
            end
        end
    end

    print("账号信息: " .. accountInfo)

    -- 动态生成输出文件路径
    local outputSubDir = outputDir .. id .. "\\游戏账号\\"
    local outputFilePath = outputSubDir .. id .. ".txt"
    print("输出文件路径: " .. outputFilePath)

    -- 确保输出目录存在
    lfs.mkdir(outputSubDir)

    -- 递归创建目录
    local function createDirectory(path)
        local parts = {}
        for part in path:gmatch("[^\\]+") do
            table.insert(parts, part)
            local dir = table.concat(parts, "\\")
            if not lfs.attributes(dir, "mode") then
                lfs.mkdir(dir)
            end
        end
    end

    createDirectory(outputSubDir)

    -- 打开输出文件
    local outputFile = io.open(outputFilePath, "w")
    if not outputFile then
        print("无法创建输出文件: " .. outputFilePath)
        break
    end

    -- 写入结果
    outputFile:write(accountInfo .. "\n")

    -- 关闭输出文件
    outputFile:close()
end

-- 关闭文件
inputFile:close()

-- 关闭 Excel 工作簿
workbook:Close(false)

-- 退出 Excel 应用程序
if excel then
    excel:Quit()
    excel = nil
end

-- 释放 COM 对象
worksheet = nil
workbook = nil