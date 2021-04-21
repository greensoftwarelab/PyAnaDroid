package com.example.sampleapp.ui.notifications;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
import com.hunter.library.debug.HunterDebug;
import android.content.Context;

public class NotificationsViewModel extends ViewModel {

    private MutableLiveData<String> mText;

    @HunterDebug
    public NotificationsViewModel() {
        mText = new MutableLiveData<>();
        mText.setValue("This is notifications fragment");
    }

    @HunterDebug
    public LiveData<String> getText() {
        return mText;
    }
}
