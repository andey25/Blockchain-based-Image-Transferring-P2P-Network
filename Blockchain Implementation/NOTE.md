## Important Note:

Depending on the OS, the code might perform differently when initiating the GUI, especially on Mac, the customtkinter and the tkinter library
sometimes may create compatibility issues. Also, how the threads have been set up for the code, might affect the performance when run on mac.
The whole code was developed mostly on linux, but also has been sufficiently tested on Mac. Working with the 'cli' command to instantiate the
client works perfectly for Mac as well, even the 'gui' works really well, but sometimes it might cause slow performance or randomly program crashing. 
And those crashes or erros are not attributed to the code, rather the kernel or OS infrastructure. In fact, the developed code is well-equiped to 
handle both 'gui' and 'cli' together, but it works only on linux. I have commented out the code for both features in client.py (86-88), you can read 
the comment. 

Should you face any such error or hangs, please use the cli argument and test the codes on cli, and you can use gui to visualize the interface.
But again, the crashes are very rare compared to the number of times I tested the code even with gui command. Out of 8-10 tests, it only crashed once.

Also, it (gui) runs better when the clients join the network together. Sometimes joining at a later time in an existing network (includes gui clients) might slow the performance.

The linked video shows 'gui' and 'cli' both arguments working alongside properly. Do not immitate the running command template shown here, as your running command will be different as you will need to pass either 'cli' or 'gui' as specific arguments when running client file.


https://drive.google.com/file/d/1YsLjEo7eabCY4slYKB-k3PHMqU2ZaUJZ/view?usp=drive_link
