using System;
using System.Collections.Generic;
using System.Linq;

namespace StarCluster.Core.Combat.Tracking;

public sealed class TacticalMapKnowledgeSnapshot
{
    internal TacticalMapKnowledgeSnapshot(
        string observerId,
        IEnumerable<TacticalMapContact> contacts,
        long trackSequence)
    {
        ObserverId = observerId;
        Contacts = Array.AsReadOnly(contacts.ToArray());
        TrackSequence = trackSequence;
    }

    public string ObserverId { get; }

    public IReadOnlyList<TacticalMapContact> Contacts { get; }

    public long TrackSequence { get; }

    public TacticalMapContact? Find(string objectId) =>
        Contacts.FirstOrDefault(contact => string.Equals(
            contact.ObjectId,
            objectId,
            StringComparison.Ordinal));
}
