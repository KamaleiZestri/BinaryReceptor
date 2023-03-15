using Desktop.Robot;
using Desktop.Robot.Extensions;

namespace BinaryReceptor
{
    public class KeyProcessor
    {
        private Robot robot;
        public KeyProcessor()
        {
            robot = new Robot();
        }

        public void typeText(string text)
        {
            robot.Type(text + "\n");
        }

        public void handleWebPage(HttpContext ctx)
        {
            typeText(ctx.Request.Query["content"].ToString());
        }
    }
}