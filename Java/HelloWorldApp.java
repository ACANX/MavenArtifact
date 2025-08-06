import java.io.File;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;

public class HelloWorldApp {
    public static void main(String[] args) {
        System.out.println("进入HelloWorldApp，开始执行业务逻辑...");
        // 创建时间格式化器 (yyyyMMdd.HHmmss.SSS)
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd.HHmmss.SSS");
        try {
            // 创建文件对象 (当前目录下的ts.txt)
            File file = new File("ts.txt");
            // 使用覆盖模式写入文件
            try (FileWriter writer = new FileWriter(file)) {
                // 写入当前时间戳
                writer.write(sdf.format(new Date()));
            }
            // 控制台输出完成信息
            System.out.println("task finished");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
