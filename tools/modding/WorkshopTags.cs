// Sets the tags of the collection's Workshop items, which SteamCMD's upload files cannot do.
// Needs the Steam client running and logged in as the items' owner. Built and run by
// scripts/workshop-tags.sh with the tags in config/workshop.json.
// Usage: WorkshopTags.exe <appid> <item id>=<tag>,<tag> [<item id>=<tag>,...]
using System;
using System.Linq;
using System.Threading;
using Steamworks;

class WorkshopTags
{
    static int Main(string[] a)
    {
        if (!SteamAPI.Init()) { Console.Error.WriteLine("SteamAPI.Init failed: is Steam running and logged in?"); return 1; }
        var app = new AppId_t(uint.Parse(a[0]));
        int failed = 0;
        foreach (var arg in a.Skip(1))
        {
            var parts = arg.Split(new[] { '=' }, 2);
            var id = new PublishedFileId_t(ulong.Parse(parts[0]));
            var tags = parts[1].Split(',').Select(t => t.Trim()).Where(t => t.Length > 0).ToList();
            var handle = SteamUGC.StartItemUpdate(app, id);
            if (!SteamUGC.SetItemTags(handle, tags)) { Console.Error.WriteLine(id + ": SetItemTags refused"); failed++; continue; }
            EResult result = EResult.k_EResultNone;
            bool done = false;
            var call = CallResult<SubmitItemUpdateResult_t>.Create((r, ioFailure) =>
            {
                result = ioFailure ? EResult.k_EResultIOFailure : r.m_eResult;
                done = true;
            });
            call.Set(SteamUGC.SubmitItemUpdate(handle, "Tags: " + string.Join(", ", tags)));
            for (int i = 0; i < 600 && !done; i++) { SteamAPI.RunCallbacks(); Thread.Sleep(100); }
            Console.WriteLine(id + ": " + (done ? result.ToString() : "timed out") + " [" + string.Join(", ", tags) + "]");
            if (result != EResult.k_EResultOK) failed++;
        }
        SteamAPI.Shutdown();
        return failed;
    }
}
