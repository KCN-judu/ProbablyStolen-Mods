// Creates or updates the Steam Workshop collection that gathers the mods, which SteamCMD cannot do.
// Needs the Steam client running and logged in as the owner. Built and run by scripts/workshop-collection.sh
// with the settings in config/workshop.json.
// Usage: WorkshopCollection.exe <appid> <collection id, 0 to create> <title file> <description file> <preview png>
//        <visibility: public|friends|private|keep> <tag>,<tag> <child id> [<child id> ...]
// Prints "collection <id>" first, so the caller can store a new id. Visibility is only changed when asked.
// Text comes from UTF-8 files: Windows passes command-line arguments through the local code page, which breaks Chinese.
using System;
using System.IO;
using System.Linq;
using System.Threading;
using Steamworks;

class WorkshopCollection
{
    static bool Wait<T>(SteamAPICall_t call, Action<T, bool> done) where T : struct
    {
        bool finished = false;
        var result = CallResult<T>.Create((r, ioFailure) => { done(r, ioFailure); finished = true; });
        result.Set(call);
        for (int i = 0; i < 1200 && !finished; i++) { SteamAPI.RunCallbacks(); Thread.Sleep(100); }
        return finished;
    }

    static int Main(string[] a)
    {
        if (!SteamAPI.Init()) { Console.Error.WriteLine("SteamAPI.Init failed: is Steam running and logged in?"); return 1; }
        try { return Run(a); }
        finally { SteamAPI.Shutdown(); }
    }

    static int Run(string[] a)
    {
        var app = new AppId_t(uint.Parse(a[0]));
        var id = new PublishedFileId_t(ulong.Parse(a[1]));
        string title = File.ReadAllText(a[2], System.Text.Encoding.UTF8).Trim(), description = File.ReadAllText(a[3], System.Text.Encoding.UTF8).Trim(), preview = Path.GetFullPath(a[4]), visibility = a[5];
        var tags = a[6].Split(',').Select(t => t.Trim()).Where(t => t.Length > 0).ToList();
        var children = a.Skip(7).Select(c => new PublishedFileId_t(ulong.Parse(c))).ToList();

        if (id.m_PublishedFileId == 0)
        {
            EResult created = EResult.k_EResultNone;
            bool legal = false;
            if (!Wait<CreateItemResult_t>(SteamUGC.CreateItem(app, EWorkshopFileType.k_EWorkshopFileTypeCollection), (r, io) =>
                {
                    created = io ? EResult.k_EResultIOFailure : r.m_eResult;
                    id = r.m_nPublishedFileId;
                    legal = r.m_bUserNeedsToAcceptWorkshopLegalAgreement;
                }) || created != EResult.k_EResultOK)
            {
                Console.Error.WriteLine("creating the collection failed: " + created);
                return 1;
            }
            if (legal) Console.Error.WriteLine("note: the Workshop legal agreement still has to be accepted on Steam");
            if (visibility == "keep") visibility = "private";
        }
        Console.WriteLine("collection " + id.m_PublishedFileId);

        var handle = SteamUGC.StartItemUpdate(app, id);
        bool ok = SteamUGC.SetItemTitle(handle, title)
            && SteamUGC.SetItemDescription(handle, description)
            && SteamUGC.SetItemPreview(handle, preview)
            && SteamUGC.SetItemTags(handle, tags);
        if (visibility != "keep")
            ok &= SteamUGC.SetItemVisibility(handle,
                visibility == "public" ? ERemoteStoragePublishedFileVisibility.k_ERemoteStoragePublishedFileVisibilityPublic
                : visibility == "friends" ? ERemoteStoragePublishedFileVisibility.k_ERemoteStoragePublishedFileVisibilityFriendsOnly
                : ERemoteStoragePublishedFileVisibility.k_ERemoteStoragePublishedFileVisibilityPrivate);
        if (!ok) { Console.Error.WriteLine("Steam refused one of the settings"); return 1; }
        EResult submitted = EResult.k_EResultNone;
        Wait<SubmitItemUpdateResult_t>(SteamUGC.SubmitItemUpdate(handle, "Collection update"), (r, io) =>
            submitted = io ? EResult.k_EResultIOFailure : r.m_eResult);
        Console.WriteLine("details: " + submitted + (visibility == "keep" ? "" : ", visibility " + visibility));

        int failed = submitted == EResult.k_EResultOK ? 0 : 1;
        foreach (var child in children)
        {
            EResult added = EResult.k_EResultNone;
            Wait<AddUGCDependencyResult_t>(SteamUGC.AddDependency(id, child), (r, io) =>
                added = io ? EResult.k_EResultIOFailure : r.m_eResult);
            // An item already in the collection comes back as a duplicate; that is fine on a re-run.
            bool fine = added == EResult.k_EResultOK || added == EResult.k_EResultDuplicateRequest;
            Console.WriteLine("  " + child.m_PublishedFileId + ": " + added);
            if (!fine) failed++;
        }
        return failed;
    }
}
